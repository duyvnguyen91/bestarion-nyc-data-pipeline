# Airflow Helm Release - Simple deployment
# resource "helm_release" "airflow" {
#   name             = "airflow"
#   repository       = "https://airflow.apache.org"
#   chart            = "airflow"
#   version          = "1.11.0"
#   namespace        = var.airflow_namespace
#   create_namespace = true

#   values = [
#     file("${path.module}/airflow.yaml")
#   ]

#   depends_on = [
#     google_container_node_pool.default_pool,
#   ]
# }

locals {
  airflow_metadata_conn = format(
    "postgresql://%s:%s@%s:%d/%s",
    "postgres",
    random_password.db_password.result,
    google_sql_database_instance.primary.private_ip_address,
    5432,
    "airflow"
  )
}

# Airflow Namespace
resource "kubernetes_namespace" "airflow" {
  metadata {
    name = var.airflow_namespace
  }
  depends_on = [ google_container_node_pool.default_pool ]
}

# Airflow Secret
resource "kubernetes_secret" "airflow_db_secret" {
  metadata {
    name      = "airflow-metadata-secret"
    namespace = "airflow"
  }

  data = {
    connection = local.airflow_metadata_conn
  }

  type = "Opaque"

  depends_on = [
    kubernetes_namespace.airflow
  ]
}