"""Base Agent class with tool registration, memory, and Bedrock API integration."""

from __future__ import annotations

from typing import Any

from core.bedrock_client import BedrockClient
from tools.registry import ToolRegistry


class BaseAgent:
    """Base class for all agents.

    Provides:
    - Bedrock LLM communication
    - Tool registration and execution
    - Conversation memory
    - Agentic loop (call LLM -> execute tools -> repeat until done)
    """

    name: str = "BaseAgent"
    system_prompt: str = "You are a helpful assistant."

    def __init__(
        self,
        registry: ToolRegistry,
        model: str = "haiku",
        tool_names: list[str] | None = None,
    ):
        self.llm = BedrockClient(model=model)
        self.registry = registry
        self.tool_names = tool_names  # subset of tools this agent can use
        self.memory: list[dict] = []  # conversation history

    def _get_tools(self) -> list[dict] | None:
        """Get Bedrock-formatted tools available to this agent."""
        tools = self.registry.get_bedrock_tools(self.tool_names)
        return tools if tools else None

    def _add_message(self, role: str, content: Any) -> None:
        self.memory.append({"role": role, "content": content})

    def run(self, user_message: str, max_turns: int = 10) -> str:
        """Run the agentic loop.

        1. Send user message + tools to LLM
        2. If LLM returns tool_use -> execute tools -> send results back
        3. Repeat until LLM returns text-only (end_turn) or max_turns reached

        Args:
            user_message: The user's input message.
            max_turns: Maximum LLM round-trips to prevent infinite loops.

        Returns:
            Final text response from the agent.
        """
        self._add_message("user", user_message)

        for _ in range(max_turns):
            result = self.llm.invoke(
                messages=self.memory,
                system=self.system_prompt,
                tools=self._get_tools(),
            )

            stop_reason = result.get("stop_reason", "end_turn")
            content_blocks = result.get("content", [])

            # Add assistant response to memory
            self._add_message("assistant", content_blocks)

            # If no tool use, extract text and return
            if stop_reason == "end_turn":
                return self._extract_text(content_blocks)

            # Process tool calls
            if stop_reason == "tool_use":
                tool_results = self._process_tool_calls(content_blocks)
                self._add_message("user", tool_results)

        return self._extract_text(content_blocks)

    def _process_tool_calls(self, content_blocks: list[dict]) -> list[dict]:
        """Execute all tool_use blocks and return tool results."""
        results = []
        for block in content_blocks:
            if block["type"] != "tool_use":
                continue

            tool_name = block["name"]
            tool_input = block["input"]
            tool_use_id = block["id"]

            output = self.registry.execute(tool_name, tool_input)

            results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": output,
            })
        return results

    @staticmethod
    def _extract_text(content_blocks: list[dict]) -> str:
        """Extract text from content blocks."""
        parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                parts.append(block["text"])
        return "\n".join(parts)

    def reset_memory(self) -> None:
        """Clear conversation history."""
        self.memory = []
