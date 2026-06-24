resource "aws_glue_catalog_database" "omop" {
  name = "omop_cloud_etl"
}

resource "aws_glue_catalog_table" "analytic_person" {
  database_name = aws_glue_catalog_database.omop.name
  name          = "analytic_person"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"                    = "parquet"
    "projection.enabled"                = "true"
    "projection.year_of_birth_band.type"   = "enum"
    "projection.year_of_birth_band.values" = "1900s,1910s,1920s,1930s,1940s,1950s,1960s,1970s,1980s,1990s,2000s,2010s,2020s"
    "storage.location.template"         = "s3://${var.bucket_name}/processed/analytic_person/year_of_birth_band=$${year_of_birth_band}"
  }

  storage_descriptor {
    location      = "s3://${var.bucket_name}/processed/analytic_person/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      parameters = {
        "serialization.format" = "1"
      }
    }

    columns {
      name = "person_id"
      type = "bigint"
    }
    columns {
      name = "gender"
      type = "string"
    }
    columns {
      name = "year_of_birth"
      type = "int"
    }
    columns {
      name = "race"
      type = "string"
    }
    columns {
      name = "ethnicity"
      type = "string"
    }
    columns {
      name = "visit_count"
      type = "bigint"
    }
    columns {
      name = "condition_count"
      type = "bigint"
    }
    columns {
      name = "drug_count"
      type = "bigint"
    }
    columns {
      name = "measurement_count"
      type = "bigint"
    }
    columns {
      name = "note_count"
      type = "bigint"
    }
    columns {
      name = "earliest_visit"
      type = "date"
    }
    columns {
      name = "latest_visit"
      type = "date"
    }
  }

  partition_keys {
    name = "year_of_birth_band"
    type = "string"
  }
}

resource "aws_s3_object" "etl_job_script" {
  bucket = aws_s3_bucket.pipeline.id
  key    = "scripts/etl_job.py"
  source = "${path.module}/../glue/etl_job.py"
  etag   = filemd5("${path.module}/../glue/etl_job.py")
}

resource "aws_s3_object" "pipeline_lib" {
  bucket = aws_s3_bucket.pipeline.id
  key    = "scripts/pipeline_lib.zip"
  source = "${path.module}/../glue/pipeline_lib.zip"
  etag   = filemd5("${path.module}/../glue/pipeline_lib.zip")
}

resource "aws_glue_job" "etl" {
  name     = "omop-cloud-etl"
  role_arn = aws_iam_role.glue.arn

  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/scripts/etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--extra-py-files"        = "s3://${var.bucket_name}/scripts/pipeline_lib.zip"
    "--job-bookmark-option"   = "job-bookmark-disable"
    "--S3_BUCKET"             = var.bucket_name
    "--RAW_PREFIX"            = "raw/"
    "--PROCESSED_PREFIX"      = "processed/"
    "--AWS_REGION"            = var.aws_region
    "--enable-metrics"        = "true"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  depends_on = [
    aws_s3_object.etl_job_script,
    aws_s3_object.pipeline_lib
  ]
}
