# Enable CloudSQL Admin API
resource "google_project_service" "sqladmin_api" {
  service = "sqladmin.googleapis.com"
  project = var.project_id

  disable_on_destroy = false
}

# Enable Service Networking API
resource "google_project_service" "servicenetworking_api" {
  service = "servicenetworking.googleapis.com"
  project = var.project_id

  disable_on_destroy = false
}

resource "google_compute_global_address" "cloudsql_private_range" {
  name          = "cloudsql-private-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.vpc_network_self_link

  lifecycle {
    prevent_destroy = false
  }
}

resource "google_service_networking_connection" "cloudsql_vpc_connection" {
  network                 = var.vpc_network_self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.cloudsql_private_range.name]

  depends_on = [
    google_project_service.servicenetworking_api
  ]

  lifecycle {
    prevent_destroy = false
  }
}

# CloudSQL Instance
resource "google_sql_database_instance" "primary" {
  name                = var.cloudsql_instance_name
  database_version    = var.database_version
  region              = var.region
  deletion_protection = false

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
      private_network = var.vpc_network_self_link
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
resource "google_sql_database" "airflow_database" {
  name     = var.airflow_database_name
  instance = google_sql_database_instance.primary.name
}

resource "google_sql_database" "datalake_database" {
  name     = "datalake"
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
  special = false
}

