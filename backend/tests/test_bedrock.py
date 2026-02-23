"""CHECKPOINT 1: Test Bedrock Claude connection."""

import boto3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()


def test_bedrock():
    session = boto3.Session(
        profile_name=os.getenv("AWS_PROFILE", "interview-pilot"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    client = session.client("bedrock-runtime")

    model_id = os.getenv("BEDROCK_MODEL_HAIKU")
    print(f"Testing model: {model_id}")

    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Say OK if you can hear me."}],
            }
        ),
    )

    result = json.loads(response["body"].read())
    reply = result["content"][0]["text"]
    print(f"Claude response: {reply}")
    print("[PASS] Bedrock connection SUCCESS")


if __name__ == "__main__":
    try:
        test_bedrock()
    except Exception as e:
        print(f"[FAIL] Bedrock connection FAILED: {e}")
        sys.exit(1)
