"""Tool Registry -- tool definition, dispatch, and result formatting."""

from __future__ import annotations

import json
from typing import Any, Callable


class Tool:
    """A single tool that can be registered and invoked."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable[..., Any],
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_bedrock_schema(self) -> dict:
        """Convert to Bedrock tool_use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def execute(self, **kwargs) -> str:
        """Execute the tool and return a JSON string result."""
        result = self.handler(**kwargs)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable[..., Any],
    ) -> None:
        self._tools[name] = Tool(name, description, input_schema, handler)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_bedrock_tools(self, names: list[str] | None = None) -> list[dict]:
        """Get Bedrock-formatted tool definitions.

        Args:
            names: If provided, only return these tools. Otherwise return all.
        """
        if names is None:
            return [t.to_bedrock_schema() for t in self._tools.values()]
        return [
            self._tools[n].to_bedrock_schema()
            for n in names
            if n in self._tools
        ]

    def execute(self, name: str, input_data: dict) -> str:
        """Execute a tool by name with given input."""
        tool = self._tools.get(name)
        if tool is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return tool.execute(**input_data)
        except Exception as e:
            return json.dumps({"error": f"Tool '{name}' failed: {str(e)}"})

    def tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
    ) -> Callable:
        """Decorator to register a function as a tool.

        Usage:
            @registry.tool(
                name="web_search",
                description="Search the web for information.",
                input_schema={...}
            )
            def web_search(query: str, num_results: int = 5) -> dict:
                ...
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.register(name, description, input_schema, func)
            return func
        return decorator

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


# Global registry instance
global_registry = ToolRegistry()


def register_tool(
    name: str,
    description: str,
    input_schema: dict,
) -> Callable:
    """Module-level decorator that registers to the global registry.

    Usage:
        @register_tool(
            name="web_search",
            description="Search the web for information.",
            input_schema={...}
        )
        def web_search(query: str, num_results: int = 5) -> dict:
            ...
    """
    return global_registry.tool(name, description, input_schema)
