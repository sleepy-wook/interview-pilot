"""CHECKPOINT 1: Test S3 bucket connection."""

import boto3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()


def test_s3():
    session = boto3.Session(
        profile_name=os.getenv("AWS_PROFILE", "interview-pilot"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    s3 = session.client("s3")
    bucket = os.getenv("S3_BUCKET")
    print(f"Testing bucket: {bucket}")

    # Upload test
    s3.put_object(Bucket=bucket, Key="test/hello.txt", Body=b"Hello from Interview Pilot!")
    print("  Upload: OK")

    # Download test
    response = s3.get_object(Bucket=bucket, Key="test/hello.txt")
    content = response["Body"].read().decode()
    assert content == "Hello from Interview Pilot!"
    print("  Download: OK")

    # Cleanup
    s3.delete_object(Bucket=bucket, Key="test/hello.txt")
    print("  Cleanup: OK")

    print("[PASS] S3 connection SUCCESS")


if __name__ == "__main__":
    try:
        test_s3()
    except Exception as e:
        print(f"[FAIL] S3 connection FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. Bucket name correct?")
        print("  2. IAM user has S3 permissions?")
        sys.exit(1)
