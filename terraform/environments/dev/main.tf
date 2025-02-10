# terraforｍ/environments/dev/main.tf
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.14.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.14.0"
    }
  }

  backend "local" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# プロジェクト変数の定義
variable "project_id" {
  description = "GCPプロジェクトID"
  type        = string
}

variable "region" {
  description = "デフォルトのリージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "db_password" {
  description = "データベースユーザーのパスワード"
  type        = string
  sensitive   = true
}

# Storage Module
module "storage" {
  source      = "../../modules/storage"
  project_id  = var.project_id
  environment = "dev"
}

# CloudSQL Module
module "cloudsql" {
  source      = "../../modules/cloudsql"
  project_id  = var.project_id
  region      = var.region
  environment = "dev"
  db_password = var.db_password
}

# Functions Module
module "functions" {
  source      = "../../modules/functions"
  project_id  = var.project_id
  region      = var.region
  environment = "dev"
  
  # Cloud SQL接続情報
  db_instance_connection_name = module.cloudsql.instance_connection_name
  db_name                    = module.cloudsql.database_name
  db_user                    = module.cloudsql.database_user
  db_password               = var.db_password
  
  depends_on  = [module.storage, module.cloudsql]
}

# API Gateway Module
module "api_gateway" {
  source                   = "../../modules/api_gateway"
  project_id               = var.project_id
  region                   = var.region
  environment              = "dev"
  chat_message_function_url = module.functions.chat_message_function_url
  depends_on               = [module.functions]
}

# Vertex AI Module (Gemini APIのみ)
module "vertex_ai" {
  source      = "../../modules/vertex_ai"
  project_id  = var.project_id
  region      = var.region
  environment = "dev"
}

variable "create_instance" {
  description = "Whether to create a new instance or use existing one"
  type        = bool
  default     = true
}

# 出力定義
output "api_gateway_url" {
  value = module.api_gateway.gateway_url
}

output "chat_message_function_url" {
  value = module.functions.chat_message_function_url
}

output "database_connection" {
  value = module.cloudsql.instance_connection_name
  sensitive = true
}