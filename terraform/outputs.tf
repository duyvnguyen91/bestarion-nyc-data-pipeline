output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
}

output "cluster_location" {
  description = "GKE cluster location"
  value       = google_container_cluster.primary.location
}

output "cloudsql_instance_name" {
  description = "CloudSQL instance name"
  value       = google_sql_database_instance.primary.name
}

output "cloudsql_connection_name" {
  description = "CloudSQL connection name"
  value       = google_sql_database_instance.primary.connection_name
}

output "cloudsql_public_ip" {
  description = "CloudSQL public IP address"
  value       = google_sql_database_instance.primary.public_ip_address
}

output "cloudsql_private_ip" {
  description = "CloudSQL private IP address"
  value       = google_sql_database_instance.primary.private_ip_address
  sensitive   = false
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "Database user name"
  value       = google_sql_user.user.name
}

output "database_password" {
  description = "Database password (sensitive)"
  value       = random_password.db_password.result
  sensitive   = true
}

output "jenkins_namespace" {
  description = "Jenkins namespace"
  value       = var.jenkins_namespace
}

output "airflow_namespace" {
  description = "Airflow namespace"
  value       = var.airflow_namespace
}

output "get_jenkins_url" {
  description = "Command to get Jenkins URL"
  value       = "kubectl get svc -n ${var.jenkins_namespace} jenkins -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
}

output "get_airflow_url" {
  description = "Command to get Airflow URL"
  value       = "kubectl get svc -n ${var.airflow_namespace} airflow-webserver -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
}

