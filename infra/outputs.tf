output "bucket_name" {
  value = aws_s3_bucket.clips.bucket
}

output "db_endpoint" {
  value = aws_db_instance.clips.address
}

output "db_port" {
  value = aws_db_instance.clips.port
}

output "app_security_group_id" {
  description = "Usar este ID al lanzar la instancia EC2 que corre docker-compose"
  value       = aws_security_group.app.id
}

output "default_subnet_id" {
  description = "Una subred publica de la VPC por defecto, util para lanzar la instancia EC2"
  value       = data.aws_subnets.default.ids[0]
}
