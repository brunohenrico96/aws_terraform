resource "aws_security_group" "alb" {
  count = var.enable_load_balancer ? 1 : 0

  name        = "${local.name_prefix}-alb-sg"
  description = "Permite trafego HTTP da internet para o ALB."
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP publico"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Saida livre do ALB"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

resource "aws_security_group" "ecs_service" {
  name        = "${local.name_prefix}-ecs-sg"
  description = "Permite trafego para as tasks do ECS."
  vpc_id      = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.enable_load_balancer ? [1] : []

    content {
      description     = "Entrada vinda do ALB"
      from_port       = var.container_port
      to_port         = var.container_port
      protocol        = "tcp"
      security_groups = [aws_security_group.alb[0].id]
    }
  }

  dynamic "ingress" {
    for_each = var.enable_load_balancer ? [] : [1]

    content {
      description = "Acesso direto ao app sem ALB"
      from_port   = var.container_port
      to_port     = var.container_port
      protocol    = "tcp"
      cidr_blocks = var.app_ingress_cidrs
    }
  }

  egress {
    description = "Saida livre das tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecs-sg"
  })
}
