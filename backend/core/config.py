from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # AWS (Named Profile — credentials are in ~/.aws/credentials)
    aws_profile: str = ""
    aws_region: str = "us-east-1"

    # Bedrock Models
    bedrock_model_haiku: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_model_sonnet: str = "us.anthropic.claude-sonnet-4-6-20250514-v1:0"

    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/interview_pilot"

    # S3
    s3_bucket: str = "interview-pilot-uploads"

    # Transcribe
    transcribe_language_code: str = "en-US"

    # App
    app_env: str = "development"
    app_password: str = ""  # If set, require this password for API access
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
