"""
Input Validation Middleware and Utilities
Provides comprehensive input validation for API requests
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import re

from config import config
from exceptions import (
    InputTooLongError,
    InvalidScamTacticError,
    PersonaNotFoundError,
    RateLimitExceededError
)


# ============================================================================
# Pydantic Models with Validation
# ============================================================================

class ValidatedMessageRequest(BaseModel):
    """Base model for message requests with validation"""
    
    message: str = Field(
        ...,
        min_length=config.validation.MIN_MESSAGE_LENGTH,
        max_length=config.validation.MAX_MESSAGE_LENGTH,
        description="User message content"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        """Validate message content"""
        # Strip whitespace
        v = v.strip()
        
        # Check if empty after stripping
        if not v:
            raise ValueError("Message cannot be empty or whitespace only")
        
        # Check for potential prompt injection
        dangerous_patterns = [
            r"ignore\s+previous\s+instructions",
            r"ignore\s+all\s+previous",
            r"disregard\s+previous",
            r"forget\s+previous",
            r"system\s*:",
            r"assistant\s*:",
            r"<\|im_start\|>",
            r"<\|im_end\|>",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Message contains potentially dangerous content")
        
        return v


class SimulationStartRequest(BaseModel):
    """Request to start a simulation"""
    
    victim_persona: str = Field(
        default="average",
        description="Victim persona type"
    )
    scam_tactic: str = Field(
        default="WhatsApp 對話詐騙",
        description="Scam tactic to use"
    )
    mode: str = Field(
        default="fast",
        pattern="^(fast|demo)$",
        description="Simulation mode: fast or demo"
    )
    auto_train: bool = Field(
        default=True,
        description="Enable auto-training after simulation"
    )
    
    @field_validator('victim_persona')
    @classmethod
    def validate_persona(cls, v: str) -> str:
        """Validate persona type"""
        if v != "random" and not config.validate_persona(v):
            raise PersonaNotFoundError(v, config.persona.AVAILABLE_PERSONAS)
        return v
    
    @field_validator('scam_tactic')
    @classmethod
    def validate_scam_tactic(cls, v: str) -> str:
        """Validate scam tactic"""
        if v != "random" and not config.validate_scam_tactic(v):
            raise InvalidScamTacticError(v, config.scam_tactics.AVAILABLE_TACTICS)
        return v


class GameMessageRequest(BaseModel):
    """Request to send message in game"""
    
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(
        ...,
        min_length=config.validation.MIN_MESSAGE_LENGTH,
        max_length=config.validation.MAX_MESSAGE_LENGTH
    )
    target_ai: str = Field(default="AI-D", pattern="^AI-[A-D]$")
    persona_type: str = Field(default="A", pattern="^[A-D]$")
    role: Optional[str] = Field(default=None, max_length=50)
    
    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id(cls, v):
        """Convert session_id to string"""
        return str(v)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content"""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class PersonalChatStartRequest(BaseModel):
    """Request to start personal chat"""
    
    mode: str = Field(
        ...,
        pattern="^(expert|scammer)$",
        description="Chat mode: expert or scammer"
    )
    scam_type: Optional[str] = Field(
        default=None,
        description="Scam type (required if mode=scammer)"
    )
    
    @field_validator('scam_type')
    @classmethod
    def validate_scam_type(cls, v: Optional[str], info) -> Optional[str]:
        """Validate scam type when mode is scammer"""
        mode = info.data.get('mode')
        if mode == 'scammer' and not v:
            raise ValueError("scam_type is required when mode is 'scammer'")
        if v and not config.validate_scam_tactic(v):
            raise InvalidScamTacticError(v, config.scam_tactics.AVAILABLE_TACTICS)
        return v


class PersonalChatMessageRequest(ValidatedMessageRequest):
    """Request to send message in personal chat"""
    
    session_id: str = Field(..., min_length=1, max_length=100)
    images: Optional[List[str]] = Field(
        default=None,
        max_length=5,
        description="Base64 encoded images (max 5)"
    )
    
    @field_validator('images')
    @classmethod
    def validate_images(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate image data"""
        if not v:
            return v
        
        # Check number of images
        if len(v) > 5:
            raise ValueError("Maximum 5 images allowed")
        
        # Check each image size (rough estimate: base64 is ~1.33x original)
        max_size = 5 * 1024 * 1024  # 5MB per image
        for img in v:
            if len(img) > max_size * 1.33:
                raise ValueError(f"Image too large (max {max_size // 1024 // 1024}MB)")
        
        return v


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: dict = {}  # {ip: [(timestamp, count)]}
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client has exceeded rate limit
        
        Returns:
            True if within limit, False if exceeded
        """
        import time
        
        now = time.time()
        window = config.validation.RATE_LIMIT_WINDOW_SECONDS
        limit = config.validation.RATE_LIMIT_REQUESTS
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if now - ts < window
            ]
        else:
            self.requests[client_ip] = []
        
        # Count requests in current window
        total_requests = sum(count for _, count in self.requests[client_ip])
        
        if total_requests >= limit:
            return False
        
        # Add current request
        self.requests[client_ip].append((now, 1))
        return True
    
    def get_retry_after(self, client_ip: str) -> int:
        """Get seconds until rate limit resets"""
        import time
        
        if client_ip not in self.requests or not self.requests[client_ip]:
            return 0
        
        oldest_request = min(ts for ts, _ in self.requests[client_ip])
        window = config.validation.RATE_LIMIT_WINDOW_SECONDS
        retry_after = int(window - (time.time() - oldest_request))
        
        return max(0, retry_after)


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============================================================================
# Middleware
# ============================================================================

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host
    
    # Check rate limit
    if not rate_limiter.check_rate_limit(client_ip):
        retry_after = rate_limiter.get_retry_after(client_ip)
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please try again in {retry_after} seconds.",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    return await call_next(request)


async def validation_error_handler(request: Request, exc: Exception):
    """Handle validation errors"""
    
    if isinstance(exc, InputTooLongError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Input too long",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    if isinstance(exc, PersonaNotFoundError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid persona",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    if isinstance(exc, InvalidScamTacticError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid scam tactic",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    # Generic validation error
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation error",
            "message": str(exc)
        }
    )


# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_output(text: str) -> str:
    """Sanitize output text (remove potential XSS)"""
    # Basic HTML escaping
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    return text


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format"""
    # UUID format: 8-4-4-4-12 hex digits
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, session_id, re.IGNORECASE))


def truncate_long_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
