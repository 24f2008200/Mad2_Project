# backend/utils/storage.py
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from datetime import timedelta

S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_PREFIX = os.getenv("S3_EXPORT_PREFIX", "exports/")  # e.g. exports/
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def s3_client():
    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

def upload_file_to_s3(local_path: str, key: str) -> str:
    """
    Upload a local file to S3. Returns the S3 object key.
    """
    client = s3_client()
    bucket = S3_BUCKET
    if not bucket:
        raise ValueError("S3_BUCKET not configured")

    try:
        client.upload_file(local_path, bucket, key)
    except (BotoCoreError, ClientError) as e:
        raise

    return key

def presigned_url_for_key(key: str, expires_in: int = 3600*24) -> str:
    """
    Generate a presigned GET URL (default expiry 24 hours).
    """
    client = s3_client()
    bucket = S3_BUCKET
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as e:
        raise
    return url
