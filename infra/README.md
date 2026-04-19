# Infraestrutura

Cada pasta dentro de `infra/` representa uma stack Terraform independente.

- `calculadora_financeira/`: stack do ECS Fargate, ALB, IAM, ECR e rede da calculadora.
- `transfermarkt/`: stack do Glue/S3 do projeto de dados.

Entre na pasta da stack que deseja operar antes de rodar `terraform init`, `plan` ou `apply`.
