"""
Base class for all anti-fraud AI agents.
Simplified for Vertex AI only (no ADK dependency).
"""


class BaseAntifraudAgent:
    """
    Shared base for ScammerAgent, ExpertAgent, VictimAgent, RecorderAgent.
    
    Provides a single `_init_agent()` helper that sets agent attributes.
    Subclasses should call self._init_agent(...) at the end of their __init__.
    """

    # Allow extra fields for flexibility
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
            model:       LLM instance (VertexAILLM).
            instruction: System instruction / prompt string.
            tools:       Optional list of tool callables.
        """
        tools = tools or []
        
        # 直接設置屬性
        self.name = name
        self.model = model
        self.instruction = instruction
        self.tools = tools
        self.app_name = "agents"
