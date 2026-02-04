"""
Prompt 模組 - 提供結構化的 Prompt 範例和建構工具
"""

from .expert_examples import EXPERT_EXAMPLES
from .scammer_examples import SCAMMER_EXAMPLES
from .victim_examples import VICTIM_EXAMPLES
from .prompt_builder import PromptBuilder

__all__ = [
    'EXPERT_EXAMPLES',
    'SCAMMER_EXAMPLES', 
    'VICTIM_EXAMPLES',
    'PromptBuilder'
]
