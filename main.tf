terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Aqui configuramos o Backend (onde a memória do Terraform vai ficar)
  backend "s3" {
    bucket = "meu-terraform-state-bruno" # Coloque o nome do seu bucket aqui
    key    = "transfermarkt/terraform.tfstate"
    region = "us-east-1" # Coloque a sua região
  }
}

provider "aws" {
  region = "us-east-1"
}
