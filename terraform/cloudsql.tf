# Enable CloudSQL Admin API
resource "google_project_service" "sqladmin_api" {
  service = "sqladmin.googleapis.com"
  project = var.project_id

  disable_on_destroy = false
}

# CloudSQL Instance
resource "google_sql_database_instance" "primary" {
  name             = var.cloudsql_instance_name
  database_version = var.database_version
  region           = var.region

  settings {
    tier                        = var.database_tier
    deletion_protection_enabled = false
    availability_type           = "ZONAL"

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = null
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  depends_on = [
    google_project_service.sqladmin_api,
  ]
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.primary.name
}

# Database User
resource "google_sql_user" "user" {
  name     = var.database_user
  instance = google_sql_database_instance.primary.name
  password = random_password.db_password.result
}

# Generate random password for database user
resource "random_password" "db_password" {
  length  = 16
  special = true
}

