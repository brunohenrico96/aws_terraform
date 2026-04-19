resource "aws_glue_job" "extract_transfermarkt" {
  name     = "job_extract_transfermarkt"
  role_arn = aws_iam_role.glue_transfermarkt_role.arn

  # Usa a versao visual do Glue / Spark mais recente
  glue_version = "4.0"

  command {
    # Usamos pythonshell para scripts leves de extracao
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://${aws_s3_object.glue_extracao_script.bucket}/${aws_s3_object.glue_extracao_script.key}"
  }

  default_arguments = {
    "--TempDir"                   = "s3://${aws_s3_bucket.scripts_bucket.bucket}/temp/"
    "--additional-python-modules" = "awswrangler==3.9.1,pyarrow==15.0.0,beautifulsoup4==4.12.2,requests==2.31.0"
    "--selecao_id"                = "3439"
    "--database_name"             = aws_glue_catalog_database.transfermarkt_db.name
    "--output_bucket"             = aws_s3_bucket.data_bucket.bucket
  }

  max_capacity = 0.0625
}
