"""
Custom Exception Classes for AI Anti-Fraud Platform
Provides specific, actionable error types for better error handling
"""


class AntiFraudException(Exception):
    """Base exception for all anti-fraud platform errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# Agent-Related Exceptions
# ============================================================================

class AgentException(AntiFraudException):
    """Base exception for agent-related errors"""
    pass


class AgentInitializationError(AgentException):
    """Raised when agent fails to initialize"""
    pass


class AgentResponseError(AgentException):
    """Raised when agent fails to generate response"""
    pass


class RoleConsistencyError(AgentException):
    """Raised when agent violates role consistency rules"""
    def __init__(self, agent_type: str, violations: list, original_response: str):
        self.agent_type = agent_type
        self.violations = violations
        self.original_response = original_response
        message = f"{agent_type} violated role consistency: {', '.join(violations)}"
        super().__init__(message, {
            "agent_type": agent_type,
            "violations": violations,
            "response_preview": original_response[:100]
        })


class PersonaNotFoundError(AgentException):
    """Raised when requested persona type doesn't exist"""
    def __init__(self, persona_type: str, available_personas: list):
        self.persona_type = persona_type
        self.available_personas = available_personas
        message = f"Persona '{persona_type}' not found. Available: {', '.join(available_personas)}"
        super().__init__(message, {
            "requested": persona_type,
            "available": available_personas
        })


# ============================================================================
# LLM-Related Exceptions
# ============================================================================

class LLMException(AntiFraudException):
    """Base exception for LLM-related errors"""
    pass


class OllamaConnectionError(LLMException):
    """Raised when cannot connect to Ollama service"""
    def __init__(self, base_url: str, original_error: Exception):
        self.base_url = base_url
        self.original_error = original_error
        message = f"Cannot connect to Ollama at {base_url}: {str(original_error)}"
        super().__init__(message, {
            "base_url": base_url,
            "error_type": type(original_error).__name__
        })


class ModelNotFoundError(LLMException):
    """Raised when requested model is not available"""
    def __init__(self, model_name: str, base_url: str):
        self.model_name = model_name
        self.base_url = base_url
        message = f"Model '{model_name}' not found on Ollama server at {base_url}"
        super().__init__(message, {
            "model": model_name,
            "server": base_url
        })


class LLMTimeoutError(LLMException):
    """Raised when LLM request times out"""
    def __init__(self, timeout_seconds: float, model_name: str):
        self.timeout_seconds = timeout_seconds
        self.model_name = model_name
        message = f"LLM request timed out after {timeout_seconds}s (model: {model_name})"
        super().__init__(message, {
            "timeout": timeout_seconds,
            "model": model_name
        })


class LLMResponseTooLongError(LLMException):
    """Raised when LLM generates excessively long response"""
    def __init__(self, response_length: int, max_length: int):
        self.response_length = response_length
        self.max_length = max_length
        message = f"LLM response too long: {response_length} chars (max: {max_length})"
        super().__init__(message, {
            "actual": response_length,
            "max": max_length
        })


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseException(AntiFraudException):
    """Base exception for database-related errors"""
    pass


class SessionNotFoundError(DatabaseException):
    """Raised when session ID doesn't exist"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        message = f"Session '{session_id}' not found"
        super().__init__(message, {"session_id": session_id})


class DatabaseConnectionError(DatabaseException):
    """Raised when cannot connect to database"""
    def __init__(self, db_path: str, original_error: Exception):
        self.db_path = db_path
        self.original_error = original_error
        message = f"Cannot connect to database at {db_path}: {str(original_error)}"
        super().__init__(message, {
            "db_path": db_path,
            "error_type": type(original_error).__name__
        })


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationException(AntiFraudException):
    """Base exception for validation errors"""
    pass


class InputTooLongError(ValidationException):
    """Raised when user input exceeds maximum length"""
    def __init__(self, input_length: int, max_length: int):
        self.input_length = input_length
        self.max_length = max_length
        message = f"Input too long: {input_length} chars (max: {max_length})"
        super().__init__(message, {
            "actual": input_length,
            "max": max_length
        })


class InvalidScamTacticError(ValidationException):
    """Raised when scam tactic is not recognized"""
    def __init__(self, tactic: str, available_tactics: list):
        self.tactic = tactic
        self.available_tactics = available_tactics
        message = f"Invalid scam tactic: '{tactic}'"
        super().__init__(message, {
            "requested": tactic,
            "available": available_tactics
        })


# ============================================================================
# Simulation Exceptions
# ============================================================================

class SimulationException(AntiFraudException):
    """Base exception for simulation-related errors"""
    pass


class SimulationNotFoundError(SimulationException):
    """Raised when simulation ID doesn't exist"""
    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        message = f"Simulation '{simulation_id}' not found"
        super().__init__(message, {"simulation_id": simulation_id})


class SimulationAlreadyStoppedError(SimulationException):
    """Raised when trying to stop an already stopped simulation"""
    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        message = f"Simulation '{simulation_id}' is already stopped"
        super().__init__(message, {"simulation_id": simulation_id})


class MaxRoundsExceededError(SimulationException):
    """Raised when simulation exceeds maximum rounds"""
    def __init__(self, current_round: int, max_rounds: int):
        self.current_round = current_round
        self.max_rounds = max_rounds
        message = f"Simulation exceeded max rounds: {current_round}/{max_rounds}"
        super().__init__(message, {
            "current": current_round,
            "max": max_rounds
        })


# ============================================================================
# RAG Exceptions
# ============================================================================

class RAGException(AntiFraudException):
    """Base exception for RAG-related errors"""
    pass


class VectorDBConnectionError(RAGException):
    """Raised when cannot connect to vector database"""
    def __init__(self, db_path: str, original_error: Exception):
        self.db_path = db_path
        self.original_error = original_error
        message = f"Cannot connect to vector DB at {db_path}: {str(original_error)}"
        super().__init__(message, {
            "db_path": db_path,
            "error_type": type(original_error).__name__
        })


class NoRAGResultsError(RAGException):
    """Raised when RAG query returns no results"""
    def __init__(self, query: str):
        self.query = query
        message = f"No RAG results found for query: '{query[:50]}...'"
        super().__init__(message, {"query": query[:100]})


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================

class RateLimitException(AntiFraudException):
    """Base exception for rate limiting"""
    pass


class RateLimitExceededError(RateLimitException):
    """Raised when rate limit is exceeded"""
    def __init__(self, limit: int, window_seconds: int, retry_after: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after
        message = f"Rate limit exceeded: {limit} requests per {window_seconds}s. Retry after {retry_after}s"
        super().__init__(message, {
            "limit": limit,
            "window": window_seconds,
            "retry_after": retry_after
        })
