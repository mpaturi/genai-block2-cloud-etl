variable "bucket_name" {
  description = "Name of the S3 bucket for raw and processed data"
  type        = string
  default     = "genai-block2-omop-623756711801"
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-2"
}

variable "tags" {
  description = "Default tags applied to all resources"
  type        = map(string)
  default = {
    Project = "genai-block2-cloud-etl"
    Block   = "2"
  }
}

variable "processed_lifecycle_days" {
  description = "Days before processed objects expire (cost control)"
  type        = number
  default     = 90
}
