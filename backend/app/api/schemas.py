from pydantic import BaseModel
from typing import Optional, Dict, List, Union
from enum import Enum

# used for fraud detection requests and responses
class FraudCheckRequest(BaseModel):
    entity_name: str

class FraudCheckResponse(BaseModel):
    risk_level: str
    message: str
    details: Optional[List[Dict]] = None

# used for triggering async tasks response
class TaskResponse(BaseModel):
    message: str
    task_id: str

# Multimedia processing schemas
class MediaType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    SCREEN_RECORDING = "screen_recording"

class AnalyzeTextRequest(BaseModel):
    text: str
    session_id: Optional[str] = "default"
    elder_mode: Optional[bool] = False

class AnalyzeTextResponse(BaseModel):
    response: str
    risk_assessment: Dict
    safety_suggestions: List[str]
    source: str
    metadata: Optional[Dict] = None

class SignedUploadUrlRequest(BaseModel):
    file_type: MediaType
    file_extension: str
    user_id: Optional[str] = None

class SignedUploadUrlResponse(BaseModel):
    upload_url: str
    file_id: str
    expires_in: int

class VideoAnalysisRequest(BaseModel):
    file_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = "default"

class VideoAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    summary: Optional[str] = None
    timeline: Optional[List[Dict]] = None
    risk_indicators: Optional[List[str]] = None

# Authentication schemas
class UserRegistration(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None
    elder_mode_enabled: Optional[bool] = False

class UserLogin(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    user_id: str
    token: str
    refresh_token: str
    elder_mode_enabled: bool

# Elder mode specific schemas
class ElderModeSettings(BaseModel):
    enabled: bool
    voice_enabled: bool
    large_text: bool
    high_contrast: bool
    simplified_ui: bool

class SafetySuggestion(BaseModel):
    text: str
    action: str
    priority: int