terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # Version fijada por debajo de 5.42: versiones mas nuevas del provider
      # intentan leer la configuracion de Object Lock del bucket al
      # refrescar el estado, y esa llamada esta bloqueada por una politica
      # (SCP) de AWS Academy con "explicit deny", lo que rompe cualquier
      # plan/apply posterior aunque el bucket este bien configurado.
      version = "~> 5.31.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Red: usamos la VPC y subredes por defecto de la cuenta de AWS Academy
# ---------------------------------------------------------------------------
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ---------------------------------------------------------------------------
# S3: bucket privado y cifrado para los videos originales y las miniaturas
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "clips" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_public_access_block" "clips" {
  bucket = aws_s3_bucket.clips.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "clips" {
  bucket = aws_s3_bucket.clips.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "clips" {
  bucket = aws_s3_bucket.clips.id
  versioning_configuration {
    status = "Disabled"
  }
}

# ---------------------------------------------------------------------------
# Seguridad de red: la instancia de la app, y la RDS solo alcanzable desde ella
# ---------------------------------------------------------------------------
resource "aws_security_group" "app" {
  name        = "${var.nombre_proyecto}-app-sg"
  description = "Instancia que corre docker-compose con la API y el worker"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH solo desde mi IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.mi_ip_cidr]
  }

  ingress {
    description = "API solo desde mi IP (demo)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.mi_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.nombre_proyecto}-app-sg"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.nombre_proyecto}-rds-sg"
  description = "RDS de Clips Cortos, sin acceso publico"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Postgres solo desde la instancia de la app"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.nombre_proyecto}-rds-sg"
  }
}

resource "aws_db_subnet_group" "clips" {
  name       = "${var.nombre_proyecto}-db-subnets"
  subnet_ids = data.aws_subnets.default.ids
}

# ---------------------------------------------------------------------------
# RDS: Postgres cifrado, sin acceso publico
# ---------------------------------------------------------------------------
resource "aws_db_instance" "clips" {
  identifier     = "${var.nombre_proyecto}-db"
  engine         = "postgres"
  engine_version = "16.9"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp2"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.clips.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = false

  tags = {
    Name = "${var.nombre_proyecto}-db"
  }
}
