resource "aws_athena_workgroup" "etl" {
  name          = "omop-cloud-etl"
  force_destroy = true

  configuration {
    result_configuration {
      output_location = "s3://${var.bucket_name}/athena-results/"
    }
  }
}
