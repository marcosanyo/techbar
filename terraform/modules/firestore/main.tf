# terraform/modules/firestore/main.tf

# Firestoreの有効化
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
  disable_on_destroy = false
}

# Firestoreインスタンスの作成
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
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