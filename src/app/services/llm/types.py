"""Data types for LLM service."""

from typing import Any, Protocol


class LLMResponse(Protocol):
    choices: list[Any]
