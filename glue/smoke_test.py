"""Smoke test — verify pipeline_lib.zip imports work in the Glue runtime."""

import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

sc = SparkContext()
glueContext = GlueContext(sc)
job = Job(glueContext)
job.init("omop-smoke-test", {})

print(f"Python version: {sys.version}")
print(f"Spark version: {sc.version}")

import concepts
import schemas
import transforms
import validations

print("imports OK")

job.commit()
