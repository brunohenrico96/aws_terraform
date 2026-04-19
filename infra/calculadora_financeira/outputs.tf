output "alb_dns_name" {
  description = "DNS publico do Application Load Balancer."
  value       = var.enable_load_balancer ? aws_lb.main[0].dns_name : null
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

output "load_balancer_enabled" {
  description = "Indica se o ALB esta habilitado na stack."
  value       = var.enable_load_balancer
}

output "direct_app_access_port" {
  description = "Porta usada para acesso direto ao app quando o ALB estiver desativado."
  value       = var.enable_load_balancer ? null : var.container_port
}

output "direct_app_access_note" {
  description = "Instrucao para localizar o IP publico da task quando o app estiver sem ALB."
  value = var.enable_load_balancer ? null : "Com o ALB desativado, abra o ECS no console AWS, entre no cluster, abra a task em execucao e consulte o ENI/IP publico anexado para acessar http://IP_PUBLICO:${var.container_port}."
}
