# Bucket para armazenar os scripts Python
resource "aws_s3_bucket" "scripts_bucket" {
  bucket = "meu-transfermarkt-scripts-bruno"
}

# Bucket para armazenar os dados em Parquet/Iceberg
resource "aws_s3_bucket" "data_bucket" {
  bucket = "meu-transfermarkt-data-bruno"
}

resource "aws_s3_bucket_public_access_block" "scripts_bucket" {
  bucket = aws_s3_bucket.scripts_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts_bucket" {
  bucket = aws_s3_bucket.scripts_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Publica o script do Glue no S3 a cada apply (etag muda quando o arquivo muda)
resource "aws_s3_object" "glue_extracao_script" {
  bucket = aws_s3_bucket.scripts_bucket.id
  key    = "scripts/extracao.py"
  source = "${path.module}/../../Scripts/futebol/transfermkt.py"
  etag   = filemd5("${path.module}/../../Scripts/futebol/transfermkt.py")

  depends_on = [
    aws_s3_bucket_server_side_encryption_configuration.scripts_bucket,
  ]
}
