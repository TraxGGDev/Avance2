variable "aws_region" {
  description = "Region de AWS donde se crean los recursos"
  type        = string
  default     = "us-east-1"
}

variable "nombre_proyecto" {
  description = "Prefijo usado para nombrar los recursos (sin espacios ni mayusculas)"
  type        = string
}

variable "bucket_name" {
  description = "Nombre del bucket de S3 (debe ser globalmente unico)"
  type        = string
}

variable "db_username" {
  description = "Usuario administrador de la base de datos RDS"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Password del usuario administrador de RDS"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Nombre de la base de datos inicial"
  type        = string
  default     = "clips"
}

variable "mi_ip_cidr" {
  description = "Tu IP publica en formato CIDR (ej. 200.1.2.3/32), para permitir SSH y el puerto 8000 solo desde tu maquina"
  type        = string
}
