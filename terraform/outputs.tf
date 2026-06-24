output "bucket_arn" {
  description = "ARN of the pipeline S3 bucket"
  value       = aws_s3_bucket.pipeline.arn
}

output "glue_job_name" {
  description = "Name of the Glue ETL job"
  value       = aws_glue_job.etl.name
}

output "athena_workgroup" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.etl.name
}
