resource "aws_glue_catalog_database" "transfermarkt_db" {
  name        = "db_transfermarkt"
  description = "Banco de dados logico para o projeto Transfermarkt"
}
