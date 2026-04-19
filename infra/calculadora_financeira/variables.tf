variable "aws_region" {
  description = "Regiao onde a stack sera criada."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome do projeto usado em tags e nomes de recursos."
  type        = string
  default     = "calculadora-financeira"
}

variable "environment" {
  description = "Ambiente da stack."
  type        = string
  default     = "dev"
}

variable "container_port" {
  description = "Porta exposta pelo container."
  type        = number
  default     = 8501
}

variable "desired_count" {
  description = "Numero de tasks desejadas no ECS."
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU da task Fargate."
  type        = number
  default     = 1024
}

variable "memory" {
  description = "Memoria da task Fargate em MiB."
  type        = number
  default     = 2048
}

variable "vpc_cidr" {
  description = "CIDR principal da VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDRs das subnets publicas."
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "availability_zones" {
  description = "Availability Zones usadas pelas subnets publicas."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "container_image_tag" {
  description = "Tag da imagem publicada no ECR."
  type        = string
  default     = "latest"
}

variable "health_check_path" {
  description = "Endpoint usado pelo ALB para verificar saude do app."
  type        = string
  default     = "/_stcore/health"
}

variable "enable_stickiness" {
  description = "Habilita afinidade de sessao no target group. Streamlit se beneficia disso ao escalar."
  type        = bool
  default     = true
}

variable "enable_load_balancer" {
  description = "Mantem o ALB ativo na frente do ECS. Desative para reduzir custo e acessar o app direto pela porta 8501."
  type        = bool
  default     = false
}

variable "app_ingress_cidrs" {
  description = "CIDRs autorizados a acessar o app diretamente quando o ALB estiver desativado."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
