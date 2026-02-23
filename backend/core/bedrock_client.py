"""Amazon Bedrock client wrapper for Claude API calls."""

import json
from typing import Any

import boto3

from core.config import get_settings


class BedrockClient:
    """Wrapper for Bedrock Claude API calls with tool_use support."""

    def __init__(self, model: str = "haiku"):
        settings = get_settings()
        session_kwargs = {"region_name": settings.aws_region}
        if settings.aws_profile:
            session_kwargs["profile_name"] = settings.aws_profile
        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")
        if model == "sonnet":
            self.model_id = settings.bedrock_model_sonnet
        else:
            self.model_id = settings.bedrock_model_haiku

    def invoke(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Send a message to Claude and return the full response.

        Args:
            messages: Conversation messages [{role, content}].
            system: System prompt.
            tools: Tool definitions for tool_use.
            max_tokens: Max output tokens.
            temperature: Sampling temperature.

        Returns:
            Full Bedrock response dict with 'content', 'stop_reason', etc.
        """
        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = tools

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        return json.loads(response["body"].read())

    def converse(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> tuple[str, list[dict]]:
        """Convenience method: returns (text_reply, tool_use_blocks).

        Returns:
            Tuple of (text_content, tool_use_blocks).
            text_content: Concatenated text from all text blocks.
            tool_use_blocks: List of tool_use content blocks (may be empty).
        """
        result = self.invoke(messages, system, tools, max_tokens, temperature)

        text_parts = []
        tool_uses = []
        for block in result.get("content", []):
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_uses.append(block)

        return "\n".join(text_parts), tool_uses
