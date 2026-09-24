output "vpc_id" {
  value       = aws_vpc.flowmesh_vpc.id
  description = "FlowMesh VPC identifier"
}

output "database_endpoint" {
  value       = aws_db_instance.flowmesh_postgres.endpoint
  description = "Host and port for the managed PostgreSQL RDS instance"
}

output "database_connection_url" {
  value       = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.flowmesh_postgres.endpoint}/${var.db_name}"
  sensitive   = true
  description = "Full asyncpg connection string for FlowMesh API service"
}

output "master_kek_secret_arn" {
  value       = aws_secretsmanager_secret.flowmesh_kek.arn
  description = "ARN of Secrets Manager secret containing Master KEK"
}
