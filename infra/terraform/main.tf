terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# 1. FlowMesh Isolated VPC
resource "aws_vpc" "flowmesh_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "flowmesh-${var.environment}-vpc"
    Environment = var.environment
    Platform    = "flowmesh"
  }
}

# 2. Subnets
resource "aws_subnet" "public_subnet_a" {
  vpc_id            = aws_vpc.flowmesh_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone = "${var.region}a"
  tags = {
    Name = "flowmesh-public-a"
  }
}

resource "aws_subnet" "private_subnet_a" {
  vpc_id            = aws_vpc.flowmesh_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 10)
  availability_zone = "${var.region}a"
  tags = {
    Name = "flowmesh-private-a"
  }
}

resource "aws_subnet" "private_subnet_b" {
  vpc_id            = aws_vpc.flowmesh_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 11)
  availability_zone = "${var.region}b"
  tags = {
    Name = "flowmesh-private-b"
  }
}

# 3. Database Subnet Group
resource "aws_db_subnet_group" "flowmesh_db_subnet_group" {
  name       = "flowmesh-${var.environment}-db-subnets"
  subnet_ids = [aws_subnet.private_subnet_a.id, aws_subnet.private_subnet_b.id]

  tags = {
    Name = "FlowMesh DB Subnet Group"
  }
}

# 4. Security Group for Managed PostgreSQL
resource "aws_security_group" "db_sg" {
  name        = "flowmesh-${var.environment}-db-sg"
  description = "Controls inbound traffic to FlowMesh PostgreSQL"
  vpc_id      = aws_vpc.flowmesh_vpc.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Postgres access within FlowMesh VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 5. Managed PostgreSQL RDS Instance (System of Record)
resource "aws_db_instance" "flowmesh_postgres" {
  identifier             = "flowmesh-${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = 200
  storage_type           = "gp3"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.flowmesh_db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot    = true
  deletion_protection    = var.environment == "production"

  tags = {
    Environment = var.environment
    Component   = "system-of-record"
  }
}

# 6. AWS Secrets Manager Secret for Envelope Encryption Master Key (KEK)
resource "aws_secretsmanager_secret" "flowmesh_kek" {
  name                    = "flowmesh/${var.environment}/master-kek"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "flowmesh_kek_val" {
  secret_id     = aws_secretsmanager_secret.flowmesh_kek.id
  secret_string = jsonencode({
    ENCRYPTION_MASTER_KEY = var.master_encryption_key
  })
}
