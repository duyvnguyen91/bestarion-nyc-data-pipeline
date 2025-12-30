# Jenkins Helm Release
resource "helm_release" "jenkins" {
  name             = "jenkins"
  repository       = "https://charts.jenkins.io"
  chart            = "jenkins"
  version          = "5.8.114"
  namespace        = var.jenkins_namespace
  create_namespace = true

  # values = [
  #   file("${path.module}/jenkins.yaml")
  # ]

  depends_on = [
    google_container_node_pool.default_pool,
  ]
}

resource "google_service_account" "jenkins" {
  account_id   = "jenkins"
  display_name = "Jenkins Workload Identity SA"
}

resource "google_artifact_registry_repository_iam_member" "jenkins_push_airflow" {
  project    = var.project_id
  location   = "asia-east1"
  repository = "airflow"

  role   = "roles/artifactregistry.writer"
  member = "serviceAccount:${google_service_account.jenkins.email}"
}

resource "google_service_account_iam_member" "jenkins_wi" {
  service_account_id = google_service_account.jenkins.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[jenkins/jenkins]"
}