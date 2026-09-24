terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }
}

variable "project_id" {
  default = "flowmesh-enterprise"
}

variable "region" {
  default = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Google Kubernetes Engine (GKE) Cluster
resource "google_container_cluster" "primary" {
  name     = "flowmesh-gke-cluster"
  location = var.region
  
  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "flowmesh-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "e2-standard-4"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "flowmesh-cloud-sql"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-custom-4-16384"
    availability_type = "REGIONAL"
    backup_configuration {
      enabled = true
      point_in_time_recovery_enabled = true
    }
  }
}

# Cloud Storage Bucket (Data Lake Parquet Archive)
resource "google_storage_bucket" "datalake" {
  name          = "${var.project_id}-analytics-lake"
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}
