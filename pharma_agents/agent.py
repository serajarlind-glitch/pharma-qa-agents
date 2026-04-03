"""
Core agent class using the Anthropic Claude API.
"""

import os
import json
from typing import Optional
from pathlib import Path

import anthropic

from pharma_agents.prompts import AGENT_PROMPTS, AGENT_ROLES


# Default model - latest Claude Sonnet for cost-effective expert responses
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class PharmaAgent:
    """A specialized pharmaceutical QA agent powered by Claude."""

    def __init__(
        self,
        role: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        client: Optional[anthropic.Anthropic] = None,
    ):
        if role not in AGENT_PROMPTS:
            available = ", ".join(AGENT_PROMPTS.keys())
            raise ValueError(f"Unknown agent role: '{role}'. Available: {available}")

        self.role = role
        self.name = AGENT_ROLES[role]["name"]
        self.title = AGENT_ROLES[role]["title"]
        self.model = model
        self.temperature = temperature
        self.system_prompt = AGENT_PROMPTS[role]
        self.client = client or anthropic.Anthropic()
        self.conversation_history: list[dict] = []

    def query(
        self,
        message: str,
        context: Optional[str] = None,
        max_tokens: int = 4096,
        keep_history: bool = False,
    ) -> str:
        """
        Send a query to this agent and get a response.

        Args:
            message: The user's query.
            context: Optional additional context (e.g. output from another agent).
            max_tokens: Maximum response length.
            keep_history: If True, maintain conversation history across calls.

        Returns:
            The agent's response text.
        """
        # Build the user message
        parts = []
        if context:
            parts.append(f"<context>\n{context}\n</context>\n")
        parts.append(message)
        full_message = "\n".join(parts)

        # Build messages list
        messages = []
        if keep_history:
            messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": full_message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=self.system_prompt,
            messages=messages,
        )

        assistant_text = response.content[0].text

        # Track history if requested
        if keep_history:
            self.conversation_history.append({"role": "user", "content": full_message})
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_text}
            )

        return assistant_text

    def clear_history(self):
        """Reset conversation history."""
        self.conversation_history = []

    def __repr__(self):
        return f"PharmaAgent(role='{self.role}', name='{self.name}')"
