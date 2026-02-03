"""
Configuration Management for AI Anti-Fraud Platform
Centralizes all magic numbers and configuration values
"""

import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Trust System Configuration
# ============================================================================

@dataclass
class TrustConfig:
    """Configuration for victim trust system"""
    
    # Trust thresholds for outcomes
    SCAMMER_WIN_THRESHOLD: int = 80  # Victim trust in scammer >= 80 → scammer wins
    EXPERT_WIN_THRESHOLD: int = 75   # Victim trust in expert >= 75 → expert wins
    SCAMMER_LOSE_THRESHOLD: int = 40  # Trust in scammer < 40 (with high expert trust) → expert wins
    HIGH_ALERTNESS_THRESHOLD: int = 80  # Alertness >= 80 → victim self-protects
    
    # Trust change limits per turn (by persona)
    MAX_TRUST_CHANGE_ELDERLY: int = 12
    MAX_TRUST_CHANGE_AVERAGE: int = 15
    MAX_TRUST_CHANGE_OVERCONFIDENT: int = 20
    MAX_TRUST_CHANGE_STUDENT: int = 15
    
    # Initial trust values by persona
    INITIAL_TRUST_ELDERLY: Dict[str, int] = None
    INITIAL_TRUST_AVERAGE: Dict[str, int] = None
    INITIAL_TRUST_OVERCONFIDENT: Dict[str, int] = None
    INITIAL_TRUST_STUDENT: Dict[str, int] = None
    
    def __post_init__(self):
        # Initialize default trust values
        self.INITIAL_TRUST_ELDERLY = {
            "scammer": 70,  # Elderly trust authority more
            "expert": 50,
            "alertness": 30
        }
        self.INITIAL_TRUST_AVERAGE = {
            "scammer": 50,
            "expert": 60,
            "alertness": 50
        }
        self.INITIAL_TRUST_OVERCONFIDENT = {
            "scammer": 30,  # Overconfident trust less
            "expert": 40,
            "alertness": 70
        }
        self.INITIAL_TRUST_STUDENT = {
            "scammer": 55,
            "expert": 45,
            "alertness": 45
        }
    
    # Inertia multipliers (harder to change high trust)
    INERTIA_HIGH_TRUST_INCREASE: float = 0.6  # -40% when trust >= 80 and increasing
    INERTIA_HIGH_TRUST_DECREASE: float = 0.5  # -50% when trust >= 80 and decreasing
    INERTIA_MID_TRUST_INCREASE: float = 0.8   # -20% when trust >= 60 and increasing
    INERTIA_MID_TRUST_DECREASE: float = 0.7   # -30% when trust >= 60 and decreasing
    
    # Fatigue multipliers (repeated tactics lose effect)
    FATIGUE_3_TIMES: float = 0.5  # -50% if tactic used 3+ times recently
    FATIGUE_2_TIMES: float = 0.7  # -30% if tactic used 2 times recently
    FATIGUE_1_TIME: float = 0.9   # -10% if tactic used 1 time recently
    
    # Emotional state multipliers
    EMOTIONAL_ANXIOUS_SCAMMER_BOOST: float = 1.3   # +30% scammer effectiveness when victim anxious
    EMOTIONAL_ANXIOUS_EXPERT_PENALTY: float = 0.8  # -20% expert effectiveness when victim anxious
    EMOTIONAL_CALM_SCAMMER_PENALTY: float = 0.8    # -20% scammer effectiveness when victim calm
    EMOTIONAL_CALM_EXPERT_BOOST: float = 1.2       # +20% expert effectiveness when victim calm
    EMOTIONAL_SUSPICIOUS_SCAMMER_PENALTY: float = 0.5  # -50% scammer effectiveness when victim suspicious
    EMOTIONAL_SUSPICIOUS_EXPERT_BOOST: float = 1.3     # +30% expert effectiveness when victim suspicious
    EMOTIONAL_PANICKED_SCAMMER_BOOST: float = 1.5      # +50% scammer effectiveness when victim panicked
    EMOTIONAL_PANICKED_EXPERT_PENALTY: float = 0.7     # -30% expert effectiveness when victim panicked


# ============================================================================
# Simulation Configuration
# ============================================================================

@dataclass
class SimulationConfig:
    """Configuration for simulation behavior"""
    
    # Round limits
    MAX_ROUNDS: int = 15
    MIN_ROUNDS: int = 3
    
    # Timing (seconds)
    FAST_MODE_DELAY: float = 0.5
    DEMO_MODE_DELAY_MIN: float = 3.0
    DEMO_MODE_DELAY_MAX: float = 5.0
    
    # Auto-training
    AUTO_TRAIN_ENABLED: bool = os.getenv("AUTO_TRAIN_ENABLED", "true").lower() == "true"
    AUTO_TRAIN_MAX_CONSECUTIVE: int = 100  # Max consecutive auto-training rounds
    
    # Outcome detection
    CHECK_OUTCOME_EVERY_N_ROUNDS: int = 1  # Check after every round


# ============================================================================
# LLM Configuration
# ============================================================================

@dataclass
class LLMConfig:
    """Configuration for LLM behavior"""
    
    # Model names
    DEFAULT_MODEL: str = os.getenv("AGENT_MODEL", "gemma3:4b")
    SCAMMER_MODEL: str = os.getenv("AGENT_MODEL_SCAMMER", DEFAULT_MODEL)
    VICTIM_MODEL: str = os.getenv("AGENT_MODEL_VICTIM", DEFAULT_MODEL)
    EXPERT_MODEL: str = os.getenv("AGENT_MODEL_EXPERT", DEFAULT_MODEL)
    RECORDER_MODEL: str = os.getenv("AGENT_MODEL_RECORDER", DEFAULT_MODEL)
    
    # Ollama URLs
    DEFAULT_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    SCAMMER_BASE_URL: str = os.getenv("OLLAMA_BASE_URL_SCAMMER", DEFAULT_BASE_URL)
    VICTIM_BASE_URL: str = os.getenv("OLLAMA_BASE_URL_VICTIM", DEFAULT_BASE_URL)
    EXPERT_BASE_URL: str = os.getenv("OLLAMA_BASE_URL_EXPERT", DEFAULT_BASE_URL)
    RECORDER_BASE_URL: str = os.getenv("OLLAMA_BASE_URL_RECORDER", DEFAULT_BASE_URL)
    
    # Generation parameters
    TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.5"))
    TOP_P: float = float(os.getenv("OLLAMA_TOP_P", "0.85"))
    REPEAT_PENALTY: float = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))
    NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
    NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "2000"))
    
    # Timeouts (seconds)
    GENERATION_TIMEOUT: float = 300.0
    CONNECTION_TIMEOUT: float = 30.0
    PULL_TIMEOUT: float = 900.0
    
    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY_INITIAL: float = 1.0
    RETRY_DELAY_MULTIPLIER: float = 2.0  # Exponential backoff
    
    # Response limits
    MAX_RESPONSE_LENGTH: int = 5000  # Characters
    MAX_REASONABLE_LENGTH: int = 5000  # Warn if exceeded
    
    # Auto-pull
    AUTO_PULL_MODELS: bool = os.getenv("OLLAMA_AUTO_PULL", "1") != "0"


# ============================================================================
# Validation Configuration
# ============================================================================

@dataclass
class ValidationConfig:
    """Configuration for input validation"""
    
    # Message length limits
    MAX_MESSAGE_LENGTH: int = 1000
    MIN_MESSAGE_LENGTH: int = 1
    
    # Session limits
    MAX_CONVERSATION_HISTORY: int = 50  # Max messages to keep in history
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Prompt length limits
    MAX_PROMPT_LENGTH: int = 6000  # Warn if exceeded
    CONTEXT_SUMMARY_THRESHOLD: int = 4000  # Summarize if exceeded


# ============================================================================
# Database Configuration
# ============================================================================

@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    
    # SQLite
    SQLITE_PATH: str = os.path.join(
        os.path.dirname(__file__), '..', 'anti_fraud_game.db'
    )
    SQLITE_TIMEOUT: float = 30.0
    
    # ChromaDB
    CHROMA_PATH: str = os.path.join(
        os.path.dirname(__file__), 'db', 'chroma_db'
    )
    CHROMA_COLLECTION_NAME: str = "scam_cases"
    
    # RAG
    RAG_DEFAULT_RESULTS: int = 3
    RAG_MAX_RESULTS: int = 10


# ============================================================================
# Persona Configuration
# ============================================================================

@dataclass
class PersonaConfig:
    """Configuration for victim personas"""
    
    AVAILABLE_PERSONAS: List[str] = None
    PERSONA_DISPLAY_NAMES: Dict[str, str] = None
    
    def __post_init__(self):
        self.AVAILABLE_PERSONAS = ["elderly", "average", "overconfident", "student"]
        self.PERSONA_DISPLAY_NAMES = {
            "elderly": "陳婆婆（長者）",
            "average": "張文軒（一般市民）",
            "overconfident": "李俊傑（過度自信者）",
            "student": "王小明（大學生）"
        }


# ============================================================================
# Scam Tactics Configuration
# ============================================================================

@dataclass
class ScamTacticsConfig:
    """Configuration for scam tactics"""
    
    AVAILABLE_TACTICS: List[str] = None
    TACTIC_CATEGORIES: Dict[str, List[str]] = None
    
    def __post_init__(self):
        self.AVAILABLE_TACTICS = [
            "假冒官員詐騙",
            "假網站冒充銀行",
            "虛假投資應用程式",
            "刷單騙案",
            "假短訊釣魚",
            "中獎詐騙",
            "虛假購物平台",
            "WhatsApp 對話詐騙",
            "愛情詐騙",
            "求職詐騙"
        ]
        
        self.TACTIC_CATEGORIES = {
            "authority": ["假冒官員詐騙", "假網站冒充銀行"],
            "investment": ["虛假投資應用程式", "刷單騙案"],
            "phishing": ["假短訊釣魚", "假網站冒充銀行"],
            "social": ["WhatsApp 對話詐騙", "愛情詐騙"],
            "opportunity": ["中獎詐騙", "求職詐騙", "虛假購物平台"]
        }


# ============================================================================
# Logging Configuration
# ============================================================================

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").upper()
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Log file paths
    LOG_DIR: str = os.path.join(os.path.dirname(__file__), 'logs')
    ERROR_LOG_FILE: str = os.path.join(LOG_DIR, 'error.log')
    ACCESS_LOG_FILE: str = os.path.join(LOG_DIR, 'access.log')


# ============================================================================
# Global Configuration Instance
# ============================================================================

class Config:
    """Global configuration object"""
    
    def __init__(self):
        """Initialize all configuration sections"""
        self.trust = TrustConfig()
        self.simulation = SimulationConfig()
        self.llm = LLMConfig()
        self.validation = ValidationConfig()
        self.database = DatabaseConfig()
        self.persona = PersonaConfig()
        self.scam_tactics = ScamTacticsConfig()
        self.logging = LoggingConfig()
        
        # Ensure log directory exists
        os.makedirs(self.logging.LOG_DIR, exist_ok=True)
    
    def get_max_trust_change(self, persona_type: str) -> int:
        """Get max trust change per turn for given persona"""
        mapping = {
            "elderly": self.trust.MAX_TRUST_CHANGE_ELDERLY,
            "average": self.trust.MAX_TRUST_CHANGE_AVERAGE,
            "overconfident": self.trust.MAX_TRUST_CHANGE_OVERCONFIDENT,
            "student": self.trust.MAX_TRUST_CHANGE_STUDENT
        }
        return mapping.get(persona_type, self.trust.MAX_TRUST_CHANGE_AVERAGE)
    
    def get_initial_trust(self, persona_type: str) -> Dict[str, int]:
        """Get initial trust values for given persona"""
        mapping = {
            "elderly": self.trust.INITIAL_TRUST_ELDERLY,
            "average": self.trust.INITIAL_TRUST_AVERAGE,
            "overconfident": self.trust.INITIAL_TRUST_OVERCONFIDENT,
            "student": self.trust.INITIAL_TRUST_STUDENT
        }
        return mapping.get(persona_type, self.trust.INITIAL_TRUST_AVERAGE)
    
    def validate_persona(self, persona_type: str) -> bool:
        """Check if persona type is valid"""
        return persona_type in self.persona.AVAILABLE_PERSONAS
    
    def validate_scam_tactic(self, tactic: str) -> bool:
        """Check if scam tactic is valid"""
        return tactic in self.scam_tactics.AVAILABLE_TACTICS or tactic == "random"


# Create global config instance
config = Config()
