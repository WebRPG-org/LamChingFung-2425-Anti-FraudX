from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging
import jwt
from datetime import datetime, timedelta
import os
from app.api.schemas import UserRegistration, UserLogin, AuthResponse, ElderModeSettings

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock user database (in production, use proper database)
users_db = {}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=AuthResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user with elder mode support."""
    try:
        # Check if user already exists
        if user_data.email in users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user (in production, hash password)
        user_id = f"user_{len(users_db) + 1}"
        users_db[user_data.email] = {
            "user_id": user_id,
            "email": user_data.email,
            "password": user_data.password,  # In production, hash this
            "display_name": user_data.display_name,
            "elder_mode_enabled": user_data.elder_mode_enabled or False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user_id}, 
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_access_token(
            data={"sub": user_id, "type": "refresh"}, 
            expires_delta=timedelta(days=7)
        )
        
        return AuthResponse(
            user_id=user_id,
            token=access_token,
            refresh_token=refresh_token,
            elder_mode_enabled=user_data.elder_mode_enabled or False
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=AuthResponse)
async def login_user(login_data: UserLogin):
    """Login user and return tokens."""
    try:
        # Check if user exists
        if login_data.email not in users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user = users_db[login_data.email]
        
        # Verify password (in production, use proper password hashing)
        if user["password"] != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user["user_id"]}, 
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_access_token(
            data={"sub": user["user_id"], "type": "refresh"}, 
            expires_delta=timedelta(days=7)
        )
        
        return AuthResponse(
            user_id=user["user_id"],
            token=access_token,
            refresh_token=refresh_token,
            elder_mode_enabled=user["elder_mode_enabled"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me")
async def get_current_user(user_id: str = Depends(verify_token)):
    """Get current user information."""
    try:
        # Find user by ID
        user = None
        for email, user_data in users_db.items():
            if user_data["user_id"] == user_id:
                user = user_data
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "elder_mode_enabled": user["elder_mode_enabled"],
            "created_at": user["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.put("/elder-mode")
async def update_elder_mode_settings(
    settings: ElderModeSettings,
    user_id: str = Depends(verify_token)
):
    """Update elder mode settings for current user."""
    try:
        # Find and update user
        for email, user_data in users_db.items():
            if user_data["user_id"] == user_id:
                user_data["elder_mode_enabled"] = settings.enabled
                break
        
        return {"message": "Elder mode settings updated successfully"}
        
    except Exception as e:
        logger.error(f"Update elder mode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update elder mode settings"
        )

@router.get("/elder-mode", response_model=ElderModeSettings)
async def get_elder_mode_settings(user_id: str = Depends(verify_token)):
    """Get elder mode settings for current user."""
    try:
        # Find user
        user = None
        for email, user_data in users_db.items():
            if user_data["user_id"] == user_id:
                user = user_data
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ElderModeSettings(
            enabled=user["elder_mode_enabled"],
            voice_enabled=True,  # Default settings
            large_text=True,
            high_contrast=True,
            simplified_ui=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get elder mode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get elder mode settings"
        )

