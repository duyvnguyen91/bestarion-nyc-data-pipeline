variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "civil-treat-482015-n6"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "asia-east1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "asia-east1-a"
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "bestarion-nyc-cluster"
}

variable "node_pool_name" {
  description = "Name of the node pool"
  type        = string
  default     = "default-node-pool"
}

variable "node_count" {
  description = "Number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type for the node pool (medium instance)"
  type        = string
  default     = "e2-medium"
}

variable "cloudsql_instance_name" {
  description = "Name of the CloudSQL instance"
  type        = string
  default     = "bestarion-nyc-db"
}

variable "database_version" {
  description = "Database version for CloudSQL"
  type        = string
  default     = "POSTGRES_15"
}

variable "database_tier" {
  description = "Tier for CloudSQL instance (small instance)"
  type        = string
  default     = "db-f1-micro"
}

variable "database_name" {
  description = "Name of the default database"
  type        = string
  default     = "bestarion_db"
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "bestarion_user"
}

variable "jenkins_namespace" {
  description = "Kubernetes namespace for Jenkins"
  type        = string
  default     = "jenkins"
}

variable "airflow_namespace" {
  description = "Kubernetes namespace for Airflow"
  type        = string
  default     = "airflow"
}

variable "enable_private_nodes" {
  description = "Enable private nodes for GKE cluster"
  type        = bool
  default     = false
}

variable "network" {
  description = "VPC network name"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "VPC subnetwork name"
  type        = string
  default     = ""
}

