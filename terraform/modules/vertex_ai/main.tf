# terraforｍ/modules/vertex_ai/main.tf
# Vertex AIのAPIを有効化
resource "google_project_service" "vertex_ai" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Gemini APIを使用するためのサービスアカウント
resource "google_service_account" "vertex_ai" {
  account_id   = "vertex-ai-${var.environment}"
  display_name = "Vertex AI Service Account ${var.environment}"
}

# サービスアカウントにVertex AI User権限を付与
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_ai.email}"
}

# Storage Viewerの権限も付与（必要に応じて）
resource "google_project_iam_member" "storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.vertex_ai.email}"
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

# 出力定義
output "service_account_email" {
  value = google_service_account.vertex_ai.email
  description = "Gemini APIを使用するためのサービスアカウントのメールアドレス"
}