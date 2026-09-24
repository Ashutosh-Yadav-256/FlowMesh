variable "environment" {
  type        = string
  default     = "production"
  description = "Target deployment environment (production, staging, dev)"
}

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "Cloud provider region for resource provisioning"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the FlowMesh VPC"
}

variable "db_instance_class" {
  type        = string
  default     = "db.t4g.medium"
  description = "RDS / Cloud SQL database instance size"
}

variable "db_allocated_storage" {
  type        = number
  default     = 50
  description = "Allocated storage in GB for PostgreSQL"
}

variable "db_name" {
  type        = string
  default     = "flowmesh"
  description = "FlowMesh primary database name"
}

variable "db_username" {
  type        = string
  default     = "flowmesh_admin"
  description = "PostgreSQL administrator username"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL administrator password"
}

variable "master_encryption_key" {
  type        = string
  sensitive   = true
  description = "Master 256-bit KEK for envelope encryption (AES-256-GCM)"
}
