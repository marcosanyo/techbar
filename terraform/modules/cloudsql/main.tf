# terraform/modules/cloudsql/main.tf

# CloudSQL APIの有効化
resource "google_project_service" "cloudsql" {
  service = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

# Get existing instance info
data "google_sql_database_instance" "instance" {
  name    = "vector-db-${var.environment}"
  project = var.project_id
  depends_on = [google_project_service.cloudsql]
}

# データベースの作成
resource "google_sql_database" "vector_database" {
  name     = "vector_db"
  instance = data.google_sql_database_instance.instance.name
  project  = var.project_id
}

# データベースユーザーの作成
resource "google_sql_user" "vector_db_user" {
  name     = "vector_user"
  instance = data.google_sql_database_instance.instance.name
  password = var.db_password
  project  = var.project_id

  lifecycle {
    ignore_changes = [
      password  # パスワードの変更を無視
    ]
  }
}

# Cloud Functions用のサービスアカウント
resource "google_service_account" "cloudsql_sa" {
  account_id   = "cloudsql-${var.environment}"
  display_name = "CloudSQL Service Account ${var.environment}"
  project      = var.project_id
}

# サービスアカウントにCloudSQL Clientロールを付与
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudsql_sa.email}"
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

variable "db_password" {
  description = "データベースユーザーのパスワード"
  type        = string
  sensitive   = true
}

# 出力定義
output "instance_connection_name" {
  value = data.google_sql_database_instance.instance.connection_name
}

output "database_name" {
  value = google_sql_database.vector_database.name
}

output "database_user" {
  value = google_sql_user.vector_db_user.name
}

output "service_account_email" {
  value = google_service_account.cloudsql_sa.email
}