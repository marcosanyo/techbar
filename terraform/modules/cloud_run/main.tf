# 必要なAPIを有効化
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com"
  ])
  
  project = var.project_id
  service = each.key
  disable_on_destroy = false
}

# Artifact Registryリポジトリの作成
resource "google_artifact_registry_repository" "chainlit" {
  provider = google-beta
  project = var.project_id
  location = var.region
  repository_id = "chainlit-${var.environment}"
  description = "Chainlitアプリケーション用のDockerリポジトリ"
  format = "DOCKER"
  depends_on = [google_project_service.required_apis]
}

# Cloud Run用のサービスアカウント
resource "google_service_account" "chainlit_run" {
  account_id   = "chainlit-run-${var.environment}"
  display_name = "Chainlit Cloud Run Service Account ${var.environment}"
  project      = var.project_id
}

# 必要な権限の付与
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.chainlit_run.email}"
}

resource "google_project_iam_member" "storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.chainlit_run.email}"
}

resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.chainlit_run.email}"
}

## Cloud Runサービス
resource "google_cloud_run_v2_service" "chainlit" {
  name     = "chainlit-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.chainlit.repository_id}/chainlit:latest"
      
      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "LOCATION"
        value = var.region
      }

      env {
        name  = "INSTANCE_CONNECTION_NAME"
        value = var.db_instance_connection_name
      }

      env {
        name  = "DB_NAME"
        value = var.db_name
      }

      env {
        name  = "DB_USER"
        value = var.db_user
      }

      env {
        name  = "DB_PASSWORD"
        value = var.db_password
      }

      env {
        name  = "HOST"
        value = "0.0.0.0"
      }

      env {
        name  = "FUNCTIONS_EMULATOR"
        value = "false"
      }
    }

    service_account = google_service_account.chainlit_run.email
  }

  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.chainlit,
    google_project_iam_member.vertex_ai_user
  ]
}

# 公開アクセスの設定
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_v2_service.chainlit.location
  project  = google_cloud_run_v2_service.chainlit.project
  service  = google_cloud_run_v2_service.chainlit.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 変数定義
variable "project_id" {
  description = "GCPプロジェクトID"
  type        = string
}

variable "region" {
  description = "リージョン"
  type        = string
}

variable "environment" {
  description = "環境(dev/stg/prod)"
  type        = string
}

variable "db_instance_connection_name" {
  description = "Cloud SQLインスタンスの接続名"
  type        = string
}

variable "db_name" {
  description = "データベース名"
  type        = string
}

variable "db_user" {
  description = "データベースユーザー"
  type        = string
}

variable "db_password" {
  description = "データベースパスワード"
  type        = string
  sensitive   = true
}

# 出力定義
output "service_url" {
  value = google_cloud_run_v2_service.chainlit.uri
}