"""
Base class for all anti-fraud AI agents.
Eliminates the duplicated ADK/non-ADK initialisation pattern (DUP-002).
"""

import os

# Attempt ADK import; fall back to plain object so agents work in Gemini mode too.
try:
    from google.adk.agents import Agent as _ADKAgent
    _BaseClass = _ADKAgent
except ImportError:
    _BaseClass = object


class BaseAntifraudAgent(_BaseClass):
    """
    Shared base for ScammerAgent, ExpertAgent, VictimAgent, RecorderAgent.

    Provides a single `_init_agent()` helper that transparently handles both:
      - ADK mode  (Ollama):  calls super().__init__() on google.adk.agents.Agent
      - Non-ADK mode (Gemini): sets attributes directly on self

    Subclasses should call self._init_agent(...) at the end of their __init__.
    """

    # Pydantic / ADK compat: allow extra fields
    class Config:
        extra = "allow"

    def _init_agent(
        self,
        name: str,
        model,
        instruction: str,
        tools: list = None,
    ) -> None:
        """
        Unified agent initialisation.

        Args:
            name:        Display name for the agent role.
            model:       LLM instance (OllamaLlm or GeminiLlm).
            instruction: System instruction / prompt string.
            tools:       Optional list of tool callables.
        """
        tools = tools or []
        if _BaseClass is not object:
            # ADK mode
            kwargs = dict(
                name=name,
                model=model,
                instruction=instruction,
                app_name="agents",
            )
            if tools:
                kwargs["tools"] = tools
            super().__init__(**kwargs)
        else:
            # Non-ADK / Gemini direct mode
            self.name = name
            self.model = model
            self.instruction = instruction
            self.tools = tools
            self.app_name = "agents"
