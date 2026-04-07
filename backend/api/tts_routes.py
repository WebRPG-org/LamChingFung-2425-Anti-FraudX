"""
Google Cloud multilingual TTS routes.
Provides role-based speech synthesis for zh-HK / zh-CN / en-US / ja-JP.
"""

from __future__ import annotations

import base64
import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from google.cloud import texttospeech
except Exception:  # pragma: no cover
    texttospeech = None


router = APIRouter(prefix="/api/tts", tags=["TTS"])


class TTSRequest(BaseModel):
    text: str
    role: Literal["scammer", "victim", "expert"]
    language: Literal["zh-HK", "zh-CN", "en-US", "ja-JP"] = "zh-HK"


class TTSResponse(BaseModel):
    success: bool
    audio_base64: str
    mime_type: str = "audio/mpeg"
    role: str
    voice_name: str
    language: str


_tts_client = None


def _get_tts_client():
    global _tts_client
    if texttospeech is None:
        raise RuntimeError("google-cloud-texttospeech is not installed")
    if _tts_client is None:
        _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client


def _voice_for_role(role: str, language: str) -> tuple[str, str]:
    if language == "zh-CN":
        env_map = {
            "scammer": os.getenv("TTS_VOICE_ZHCN_SCAMMER", "cmn-CN-Standard-B"),
            "victim": os.getenv("TTS_VOICE_ZHCN_VICTIM", "cmn-CN-Standard-A"),
            "expert": os.getenv("TTS_VOICE_ZHCN_EXPERT", "cmn-CN-Standard-D"),
        }
        return "cmn-CN", env_map.get(role, "cmn-CN-Standard-A")
    if language == "en-US":
        env_map = {
            "scammer": os.getenv("TTS_VOICE_ENUS_SCAMMER", "en-US-Standard-D"),
            "victim": os.getenv("TTS_VOICE_ENUS_VICTIM", "en-US-Standard-C"),
            "expert": os.getenv("TTS_VOICE_ENUS_EXPERT", "en-US-Standard-B"),
        }
        return "en-US", env_map.get(role, "en-US-Standard-C")
    if language == "ja-JP":
        env_map = {
            "scammer": os.getenv("TTS_VOICE_JAJP_SCAMMER", "ja-JP-Standard-C"),
            "victim": os.getenv("TTS_VOICE_JAJP_VICTIM", "ja-JP-Standard-A"),
            "expert": os.getenv("TTS_VOICE_JAJP_EXPERT", "ja-JP-Standard-B"),
        }
        return "ja-JP", env_map.get(role, "ja-JP-Standard-A")

    env_map = {
        "scammer": os.getenv("TTS_VOICE_SCAMMER", "yue-HK-Standard-B"),
        "victim": os.getenv("TTS_VOICE_VICTIM", "yue-HK-Standard-C"),
        "expert": os.getenv("TTS_VOICE_EXPERT", "yue-HK-Standard-A"),
    }
    return "yue-HK", env_map.get(role, "yue-HK-Standard-A")


def _profile_for_role(role: str) -> tuple[float, float]:
    if role == "scammer":
        return 1.03, 0.88
    if role == "victim":
        return 0.98, 1.12
    return 1.0, 0.96


@router.get("/voices")
async def list_voices(language: str = "yue-HK"):
    """
    列出指定語言的可用聲音
    預設列出粵語 (yue-HK) 聲音包
    """
    try:
        client = _get_tts_client()
        from google.cloud.texttospeech import ListVoicesRequest
        req = ListVoicesRequest(language_code=language)
        response = client.list_voices(request=req)
        voices = [
            {
                "name": v.name,
                "language_codes": list(v.language_codes),
                "ssml_gender": str(v.ssml_gender),
                "natural_sample_rate_hertz": v.natural_sample_rate_hertz,
            }
            for v in response.voices
        ]
        return {"success": True, "language": language, "voice_count": len(voices), "voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@router.get("/test")
async def test_tts(
    role: str = "scammer",
    language: str = "zh-HK",
    text: str = "你好，我係防詐專家，請注意防範詐騙。"
):
    """
    測試 TTS 合成（GET 方便瀏覽器直接測試）
    返回 audio/mpeg 二進制，可在瀏覽器直接播放
    """
    from fastapi.responses import Response as FastAPIResponse

    valid_roles = {"scammer", "victim", "expert"}
    if role not in valid_roles:
        role = "expert"
    valid_langs = {"zh-HK", "zh-CN", "en-US", "ja-JP"}
    if language not in valid_langs:
        language = "zh-HK"
    text = text.strip()[:200] or "你好，測試語音合成。"

    try:
        client = _get_tts_client()
        language_code, voice_name = _voice_for_role(role, language)
        speaking_rate, pitch = _profile_for_role(role)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
        )
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return FastAPIResponse(
            content=response.audio_content,
            media_type="audio/mpeg",
            headers={"X-Voice-Name": voice_name, "X-Language": language_code},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_cantonese_tts(request: TTSRequest):
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text cannot be empty")

    # 控制最大長度，避免單次請求過大
    if len(text) > 500:
        text = text[:500]

    try:
        client = _get_tts_client()
        language_code, voice_name = _voice_for_role(request.role, request.language)
        speaking_rate, pitch = _profile_for_role(request.role)

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        return TTSResponse(
            success=True,
            audio_base64=audio_b64,
            mime_type="audio/mpeg",
            role=request.role,
            voice_name=voice_name,
            language=request.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

