locals {
  name_prefix = "${var.project_name}-${var.environment}"

  alb_name          = substr(replace("${local.name_prefix}-alb", "_", "-"), 0, 32)
  target_group_name = substr(replace("${local.name_prefix}-tg", "_", "-"), 0, 32)
  ecr_repository    = replace(var.project_name, "_", "-")

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
