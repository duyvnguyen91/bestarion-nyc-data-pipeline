#!/bin/bash

# Script to create GCS bucket for Terraform state
# Usage: ./setup-state-bucket.sh <PROJECT_ID> [BUCKET_NAME]

set -e

PROJECT_ID=${1:-""}
BUCKET_NAME=${2:-"${PROJECT_ID}-terraform-state"}

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: $0 <PROJECT_ID> [BUCKET_NAME]"
  exit 1
fi

echo "Creating GCS bucket for Terraform state..."
echo "Project ID: $PROJECT_ID"
echo "Bucket Name: $BUCKET_NAME"

# Create the bucket
echo "Creating bucket: $BUCKET_NAME"
gsutil mb -p $PROJECT_ID -c STANDARD -l asia-east1 gs://$BUCKET_NAME || {
  if [ $? -eq 1 ]; then
    echo "Bucket might already exist. Continuing..."
  else
    exit 1
  fi
}

# Enable versioning
echo "Enabling versioning on bucket..."
gsutil versioning set on gs://$BUCKET_NAME

# Enable object versioning for state locking
echo "Configuring bucket for state locking..."
gsutil lifecycle set - <<EOF gs://$BUCKET_NAME
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"numNewerVersions": 5}
    }
  ]
}
EOF

# Set uniform bucket-level access
echo "Setting uniform bucket-level access..."
gsutil uniformbucketlevelaccess set on gs://$BUCKET_NAME

echo ""
echo "✓ GCS bucket created successfully!"
echo ""

