# Terraform Infrastructure for Bestarion NYC Data Pipeline

This directory contains Terraform configurations to provision GCP infrastructure for the Bestarion NYC Data Pipeline project.

## Resources

- **GKE Cluster**: Kubernetes cluster with a node pool using spot instances (e2-medium)
- **CloudSQL**: PostgreSQL database instance (db-f1-micro)
- **Jenkins**: Deployed on GKE using Helm
- **Airflow**: Deployed on GKE using Helm, connected to CloudSQL

## Prerequisites

1. **GCP Account**: You need a GCP project with billing enabled
2. **gcloud CLI**: Install and authenticate with `gcloud auth login`
3. **Terraform**: Install Terraform >= 1.0
4. **kubectl**: For interacting with the GKE cluster
5. **Helm**: For managing Helm releases (Terraform will use Helm provider)

## Setup Instructions

### 1. Create GCS Bucket for Terraform State

First, create a GCS bucket to store Terraform state:

```bash
chmod +x setup-state-bucket.sh
./setup-state-bucket.sh bestarion
```

### 2. Configure Terraform Backend

After creating the bucket, update `backend.tf` with your bucket name:

```hcl
terraform {
  backend "gcs" {
    bucket = "YOUR_PROJECT_ID-terraform-state"
    prefix = "terraform/state"
  }
}
```

### 3. Authenticate with GCP

Terraform needs Application Default Credentials to access the GCS backend:

```bash
gcloud auth application-default login
gcloud config set project civil-treat-482015-n6
```

This will open a browser window for you to authenticate. Make sure you're logged in with an account that has access to your GCP project.

### 4. Initialize Terraform

```bash
cd terraform
terraform init
```

### 5. Apply the Configuration

```bash
terraform apply
```

This will create:
- GKE cluster with preemptible instance node pool
- CloudSQL PostgreSQL instance
- Jenkins deployment on GKE
- Airflow deployment on GKE

### Grant permission to access Artifact Registry
```bash
gcloud projects add-iam-policy-binding civil-treat-482015-n6 \
  --member="serviceAccount:gke-node-sa@civil-treat-482015-n6.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"
```

## Accessing Services

### Jenkins

After deployment, get the Jenkins URL:

```bash
kubectl get svc -n jenkins jenkins -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

Or use the Terraform output:

```bash
terraform output get_jenkins_url
```

### Airflow

Get the Airflow URL:

```bash
kubectl get svc -n airflow airflow-webserver -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

Or use the Terraform output:

```bash
terraform output get_airflow_url
```

### Database Credentials

Get the database password:

```bash
terraform output -raw database_password
```

Connect to CloudSQL
```bash
gcloud sql connect bestarion-nyc-db --user=postgres --quiet
```

## File Structure

```
terraform/
├── backend.tf              # Terraform backend configuration (GCS)
├── providers.tf            # Provider configurations
├── variables.tf            # Variable definitions
├── outputs.tf             # Output values
├── gke.tf                 # GKE cluster and node pool
├── cloudsql.tf            # CloudSQL instance
├── jenkins.tf             # Jenkins Helm deployment
├── airflow.tf             # Airflow Helm deployment
├── terraform.tfvars.example  # Example variables file
├── setup-state-bucket.sh  # Script to create GCS bucket
└── README.md              # This file
```

