terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = "http://s3.localhost.localstack.cloud:4566"
  }
}

resource "aws_s3_bucket" "public_logs" {
  bucket_prefix = "nullstate-public-logs-"
}

resource "aws_s3_bucket_public_access_block" "public_logs" {
  bucket                  = aws_s3_bucket.public_logs.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_object" "evidence" {
  bucket       = aws_s3_bucket.public_logs.id
  key          = "evidence.txt"
  content      = "nullstate public S3 evidence"
  content_type = "text/plain"
}

resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.public_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "NullstatePublicReadEvidence"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.public_logs.arn}/evidence.txt"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.public_logs]
}
