output "alb_dns_name" {
  description = "DNS publico do Application Load Balancer."
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "URL do repositorio ECR para push da imagem."
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "Nome do cluster ECS."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Nome do service ECS."
  value       = aws_ecs_service.app.name
}

output "public_subnet_ids" {
  description = "IDs das subnets publicas."
  value       = aws_subnet.public[*].id
}
