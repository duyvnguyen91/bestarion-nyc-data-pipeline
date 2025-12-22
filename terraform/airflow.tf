# Airflow Helm Release - Simple deployment
resource "helm_release" "airflow" {
  name             = "airflow"
  repository       = "https://airflow.apache.org"
  chart            = "airflow"
  version          = "1.11.0"
  namespace        = var.airflow_namespace
  create_namespace = true

  values = [
    file("${path.module}/airflow.yaml")
  ]

  depends_on = [
    google_container_node_pool.default_pool,
  ]
}

