# 1. Cria o crachá dizendo que o serviço "glue" pode usá-lo
resource "aws_iam_role" "glue_transfermarkt_role" {
  name = "GlueTransfermarktRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# 2. Anexa uma política padrão da AWS que permite ao Glue escrever logs no CloudWatch
resource "aws_iam_role_policy_attachment" "glue_service_attachment" {
  role       = aws_iam_role.glue_transfermarkt_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# 3. Acesso restrito aos buckets de scripts/dados do projeto (substitui AmazonS3FullAccess)
resource "aws_iam_role_policy" "glue_project_s3" {
  name = "GlueTransfermarktProjectS3"
  role = aws_iam_role.glue_transfermarkt_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBuckets"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:ListBucketMultipartUploads",
        ]
        Resource = [
          aws_s3_bucket.scripts_bucket.arn,
          aws_s3_bucket.data_bucket.arn,
        ]
      },
      {
        Sid    = "ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts",
        ]
        Resource = [
          "${aws_s3_bucket.scripts_bucket.arn}/*",
          "${aws_s3_bucket.data_bucket.arn}/*",
        ]
      },
    ]
  })
}
