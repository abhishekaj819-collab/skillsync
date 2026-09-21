# ==============================================================================
# Terraform Configuration: SkillSetu Cloud SQL & IAM Security Hardening
# Project: gen-lang-client-0304136646
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  default     = "gen-lang-client-0304136646"
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "asia-south1"
  description = "GCP Region (Mumbai recommended for Maharashtra LMI users)"
}

variable "instance_name" {
  type        = string
  default     = "skillsetu-db-instance"
  description = "Cloud SQL Instance Name"
}

variable "database_name" {
  type        = string
  default     = "skillsetu_db"
  description = "Application Database Name"
}

# 1. Dedicated Least-Privilege Service Account
resource "google_service_account" "backend_sa" {
  account_id   = "skillsetu-backend-sa"
  display_name = "SkillSetu Backend Cloud SQL Service Account"
  description  = "Dedicated service account with strictly limited permissions for Cloud SQL database operations."
}

# 2. IAM Role: Cloud SQL Client
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 3. IAM Role: Cloud SQL Instance User (IAM DB Auth)
resource "google_project_iam_member" "cloudsql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 4. Cloud SQL PostgreSQL 15 Instance
resource "google_sql_database_instance" "default" {
  name             = var.instance_name
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled    = true
      start_time = "02:00"
    }

    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }
  }

  deletion_protection = false
}

# 5. Database Schema Container
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.default.name
}

# 6. IAM Database User for Service Account
resource "google_sql_user" "iam_service_account_user" {
  name     = trimsuffix(google_service_account.backend_sa.email, ".gserviceaccount.com")
  instance = google_sql_database_instance.default.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

output "connection_name" {
  value       = google_sql_database_instance.default.connection_name
  description = "Cloud SQL Connection Name for use with Cloud SQL Python Connector"
}

output "service_account_email" {
  value       = google_service_account.backend_sa.email
  description = "Service Account email configured with least privilege"
}
