# Calculadora Financeira

Esta pasta concentra os artefatos de empacotamento da aplicacao para container.

## Estrutura

- `Dockerfile`: imagem usada localmente e no ECS.
- `docker-compose.yml`: sobe a aplicacao localmente para testes.

## Onde esta o codigo

O codigo da calculadora continua em `Scripts/financeiro/calculadora_financeira/`.

Mantive o codigo-fonte onde ele ja estava para evitar uma refatoracao grande agora. A parte de deploy ficou separada em `apps/`, o que facilita repetir o mesmo padrao para novas aplicacoes depois.

## Teste local

```bash
docker compose -f apps/calculadora_financeira/docker-compose.yml up --build
```
