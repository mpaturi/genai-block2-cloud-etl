resource "aws_s3_bucket" "pipeline" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_lifecycle_configuration" "pipeline" {
  bucket = aws_s3_bucket.pipeline.id

  rule {
    id     = "expire-processed"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    expiration {
      days = var.processed_lifecycle_days
    }
  }
}
