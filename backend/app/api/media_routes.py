from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import logging
import uuid
import os
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from app.api.schemas import (
    AnalyzeTextRequest, AnalyzeTextResponse, 
    SignedUploadUrlRequest, SignedUploadUrlResponse,
    VideoAnalysisRequest, VideoAnalysisResponse,
    MediaType, SafetySuggestion
)
from app.ai_service import ai_service
from app.fraud_detect import checker
# from app.crewai.analysis_crew import AnalysisCrew  # Temporarily disabled

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# AWS S3 Configuration
S3_BUCKET = os.getenv("S3_BUCKET", "ai-agent-media")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token (simplified version)"""
    # In production, implement proper JWT verification
    return "user_1"  # Mock user ID

@router.post("/analyze-text", response_model=AnalyzeTextResponse)
async def analyze_text(
    request: AnalyzeTextRequest,
    user_id: str = Depends(verify_token)
):
    """Analyze text input with elder mode support."""
    try:
        logger.info(f"Analyzing text for user {user_id}: {request.text[:100]}...")
        
        # Use existing AI service for analysis
        result = await ai_service.generate_response(request.text, request.session_id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Enhanced analysis for elder mode
        risk_assessment = {
            "risk_level": "low",  # Default
            "confidence": 0.8,
            "indicators": []
        }
        
        safety_suggestions = [
            "如遇到可疑情況，請立即停止操作",
            "不要提供個人敏感信息",
            "如有疑問，請聯繫家人或朋友"
        ]
        
        # Enhanced analysis for elder users
        if request.elder_mode:
            # Add elder-specific risk indicators
            elder_keywords = ["緊急", "立即", "限時", "保證", "免費"]
            if any(keyword in request.text for keyword in elder_keywords):
                risk_assessment["risk_level"] = "high"
                risk_assessment["indicators"].append("包含緊急用詞")
                safety_suggestions.insert(0, "⚠️ 此訊息包含緊急用詞，請特別小心")
        
        return AnalyzeTextResponse(
            response=result["response"],
            risk_assessment=risk_assessment,
            safety_suggestions=safety_suggestions,
            source="ai_analysis",
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@router.post("/get-signed-upload-url", response_model=SignedUploadUrlResponse)
async def get_signed_upload_url(
    request: SignedUploadUrlRequest,
    user_id: str = Depends(verify_token)
):
    """Generate signed URL for direct file upload to S3."""
    try:
        # Generate unique file ID
        file_id = f"{user_id}_{uuid.uuid4()}"
        file_key = f"uploads/{request.file_type.value}/{file_id}.{request.file_extension}"
        
        # Generate presigned URL for upload
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': file_key,
                'ContentType': f"{request.file_type.value}/{request.file_extension}"
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return SignedUploadUrlResponse(
            upload_url=presigned_url,
            file_id=file_id,
            expires_in=3600
        )
        
    except ClientError as e:
        logger.error(f"S3 error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")
    except Exception as e:
        logger.error(f"Upload URL generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")

@router.post("/analyze-video-summary", response_model=VideoAnalysisResponse)
async def analyze_video_summary(
    request: VideoAnalysisRequest,
    user_id: str = Depends(verify_token)
):
    """Process video analysis summary from Cloud Function."""
    try:
        logger.info(f"Processing video analysis for file {request.file_id}")
        
        # CrewAI analysis temporarily disabled due to dependency conflicts
        # TODO: Re-enable when dependency issues are resolved
        analysis_result = {
            "summary": "視頻分析功能暫時不可用，正在修復中...",
            "timeline": [],
            "risk_indicators": []
        }
        
        elder_report = {
            "summary": "視頻分析功能暫時不可用",
            "immediate_actions": ["請稍後再試", "聯繫技術支援"]
        }
        
        # Create analysis ID
        analysis_id = f"analysis_{uuid.uuid4()}"
        
        # Extract timeline from analysis
        timeline = []
        if "timeline" in analysis_result:
            timeline = analysis_result["timeline"]
        
        # Extract risk indicators
        risk_indicators = elder_report.get("immediate_actions", [])
        
        # Create summary
        summary = elder_report.get("summary", "分析完成")
        
        return VideoAnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            summary=summary,
            timeline=timeline,
            risk_indicators=risk_indicators
        )
        
    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token)
):
    """Upload and analyze image."""
    try:
        # Save uploaded file temporarily
        file_id = f"{user_id}_{uuid.uuid4()}"
        file_path = f"/tmp/{file_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # TODO: Implement image analysis using Cloud Vision API
        # For now, return mock analysis
        analysis_result = {
            "file_id": file_id,
            "analysis": "圖片分析功能開發中",
            "risk_level": "unknown",
            "suggestions": ["請提供更多文字描述以獲得更好的分析"]
        }
        
        # Clean up temporary file
        os.remove(file_path)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token)
):
    """Upload and analyze audio."""
    try:
        # Save uploaded file temporarily
        file_id = f"{user_id}_{uuid.uuid4()}"
        file_path = f"/tmp/{file_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # TODO: Implement audio transcription using Whisper
        # For now, return mock analysis
        analysis_result = {
            "file_id": file_id,
            "transcription": "音頻轉錄功能開發中",
            "analysis": "請提供文字描述以獲得更好的分析",
            "risk_level": "unknown"
        }
        
        # Clean up temporary file
        os.remove(file_path)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")

@router.get("/analysis/{analysis_id}")
async def get_analysis_result(
    analysis_id: str,
    user_id: str = Depends(verify_token)
):
    """Get analysis result by ID."""
    try:
        # TODO: Implement proper result storage and retrieval
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "result": "分析結果檢索功能開發中"
        }
        
    except Exception as e:
        logger.error(f"Get analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis result")
