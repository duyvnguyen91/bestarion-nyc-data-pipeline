terraform {
  backend "gcs" {
    bucket = "civil-treat-482015-n6-terraform-state"
    prefix = "terraform/state"
  }
}

