# Infraestrutura

Cada pasta dentro de `infra/` representa uma stack Terraform independente.

- `calculadora_financeira/`: stack do ECS Fargate, ALB, IAM, ECR e rede da calculadora.
- `transfermarkt/`: stack do Glue/S3 do projeto de dados.

Entre na pasta da stack que deseja operar antes de rodar `terraform init`, `plan` ou `apply`.

## Calculadora financeira

A stack `calculadora_financeira/` agora suporta dois modos:

- `enable_load_balancer = false`: modo mais barato. O app roda no ECS Fargate e voce acessa direto pelo IP publico da task na porta `8501`.
- `enable_load_balancer = true`: modo mais confortavel. O ALB volta a ser criado e fornece um DNS estavel para acesso HTTP.

### Modo mais barato

Para reduzir custo ao maximo sem trocar de plataforma:

- mantenha `desired_count = 1`
- use `cpu = 256`
- use `memory = 512`
- deixe `enable_load_balancer = false`

Depois do deploy, localize o IP publico da task no console da AWS:

1. ECS
2. Cluster da calculadora
3. Task em execucao
4. ENI / Network interface
5. IP publico

Entao acesse:

`http://IP_PUBLICO:8501`
