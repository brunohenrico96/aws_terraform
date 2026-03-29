resource "aws_glue_job" "extract_transfermarkt" {
  name     = "job_extract_transfermarkt"
  role_arn = aws_iam_role.glue_transfermarkt_role.arn

  # Usa a versão visual do Glue / Spark mais recente
  glue_version = "4.0"

  command {
    # Usamos pythonshell para scripts leves de extração (mais rápido e barato que Spark puro)
    # Se fosse transformação de gigabytes, usaríamos "glueetl"
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://${aws_s3_object.glue_extracao_script.bucket}/${aws_s3_object.glue_extracao_script.key}"
  }

  default_arguments = {
    "--TempDir"                     = "s3://${aws_s3_bucket.scripts_bucket.bucket}/temp/"
    # Instalamos as bibliotecas necessárias dinamicamente no momento da execução
    # Adicionamos pyarrow para resolver o conflito de encryption_properties
    "--additional-python-modules"   = "awswrangler==3.9.1,pyarrow==15.0.0,beautifulsoup4==4.12.2,requests==2.31.0"
    # Nosso parâmetro customizado (A seleção que queremos extrair)
    "--selecao_id"                  = "3439" # 3439 é o ID do Brasil na URL deles
    "--database_name"               = aws_glue_catalog_database.transfermarkt_db.name
    "--output_bucket"               = aws_s3_bucket.data_bucket.bucket
  }

  max_capacity = 0.0625 # O tamanho mínimo de máquina para um Python Shell Job (1/16 de DPU)
}