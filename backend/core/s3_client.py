"""S3 client for resume/PDF file storage."""

import uuid

import boto3

from core.config import get_settings


def _get_s3_client():
    settings = get_settings()
    session = boto3.Session(
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )
    return session.client("s3")


def upload_file(file_bytes: bytes, original_filename: str, file_type: str, session_id: str) -> str:
    """Upload a file to S3 and return the S3 key.

    Args:
        file_bytes: Raw file content.
        original_filename: Original filename for extension detection.
        file_type: "resume" or "linkedin".
        session_id: Interview session ID for organizing files.

    Returns:
        S3 key string (e.g. "sessions/{session_id}/resume/{uuid}.pdf").
    """
    settings = get_settings()
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "pdf"
    s3_key = f"sessions/{session_id}/{file_type}/{uuid.uuid4()}.{ext}"

    s3 = _get_s3_client()
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=s3_key,
        Body=file_bytes,
        ContentType="application/pdf",
    )
    return s3_key


def download_file(s3_key: str) -> bytes:
    """Download a file from S3."""
    settings = get_settings()
    s3 = _get_s3_client()
    response = s3.get_object(Bucket=settings.s3_bucket, Key=s3_key)
    return response["Body"].read()


def delete_file(s3_key: str) -> None:
    """Delete a file from S3."""
    settings = get_settings()
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.s3_bucket, Key=s3_key)
