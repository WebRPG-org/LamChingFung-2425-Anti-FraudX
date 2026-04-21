from __future__ import annotations

import base64
import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel

try:
    from google.cloud import texttospeech
except Exception:
    texttospeech = None

try:
    import boto3
except Exception:
    boto3 = None

try:
    import azure.cognitiveservices.speech as speechsdk
except Exception:
    speechsdk = None

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
    provider: str


_client_cache: dict[str, object] = {}
ALIASES = {"vertex_ai": "vertex", "google_vertex": "vertex", "amazon_bedrock": "bedrock", "azure": "azure_openai"}


def _provider() -> str:
    tts_provider = os.getenv("TTS_PROVIDER", "").strip().lower()
    ai_provider = os.getenv("AI_PROVIDER", "vertex").strip().lower()
    return ALIASES.get(tts_provider or ai_provider, tts_provider or ai_provider)


def _rate_str(rate: float) -> str:
    pct = int(round((rate - 1.0) * 100))
    return f"{pct:+d}%"


def _pitch_str(pitch: float) -> str:
    pct = int(round(pitch * 10))
    return f"{pct:+d}%"


def _profile(role: str) -> tuple[float, float]:
    if role == "scammer":
        return 1.03, 0.88
    if role == "victim":
        return 0.98, 1.12
    return 1.0, 0.96


def _voice(provider: str, role: str, language: str) -> tuple[str, str]:
    if provider == "bedrock":
        table = {
            "zh-HK": ("yue-CN", {"scammer": "Hiujin", "victim": "Hiujin", "expert": "Hiujin"}),
            "zh-CN": ("cmn-CN", {"scammer": "Zhiyu", "victim": "Zhiyu", "expert": "Zhiyu"}),
            "en-US": ("en-US", {"scammer": "Matthew", "victim": "Joanna", "expert": "Joey"}),
            "ja-JP": ("ja-JP", {"scammer": "Takumi", "victim": "Mizuki", "expert": "Takumi"}),
        }
    elif provider == "azure_openai":
        table = {
            "zh-HK": ("zh-HK", {"scammer": "zh-HK-WanLungNeural", "victim": "zh-HK-HiuMaanNeural", "expert": "zh-HK-HiuGaaiNeural"}),
            "zh-CN": ("zh-CN", {"scammer": "zh-CN-YunxiNeural", "victim": "zh-CN-XiaoxiaoNeural", "expert": "zh-CN-YunjianNeural"}),
            "en-US": ("en-US", {"scammer": "en-US-GuyNeural", "victim": "en-US-JennyNeural", "expert": "en-US-DavisNeural"}),
            "ja-JP": ("ja-JP", {"scammer": "ja-JP-KeitaNeural", "victim": "ja-JP-NanamiNeural", "expert": "ja-JP-DaichiNeural"}),
        }
    else:
        table = {
            "zh-HK": ("yue-HK", {"scammer": "yue-HK-Standard-B", "victim": "yue-HK-Standard-C", "expert": "yue-HK-Standard-A"}),
            "zh-CN": ("cmn-CN", {"scammer": "cmn-CN-Standard-B", "victim": "cmn-CN-Standard-A", "expert": "cmn-CN-Standard-D"}),
            "en-US": ("en-US", {"scammer": "en-US-Standard-D", "victim": "en-US-Standard-C", "expert": "en-US-Standard-B"}),
            "ja-JP": ("ja-JP", {"scammer": "ja-JP-Standard-C", "victim": "ja-JP-Standard-A", "expert": "ja-JP-Standard-B"}),
        }
    lang, voices = table.get(language, table["zh-HK"])
    return lang, voices.get(role, list(voices.values())[0])


def _client(provider: str):
    cached = _client_cache.get(provider)
    if cached is not None:
        return cached
    if provider == "vertex":
        if texttospeech is None:
            raise RuntimeError("google-cloud-texttospeech is not installed")
        cached = texttospeech.TextToSpeechClient()
    elif provider == "bedrock":
        if boto3 is None:
            raise RuntimeError("boto3 is not installed")
        cached = boto3.client("polly", region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "ap-east-1")))
    elif provider == "azure_openai":
        if speechsdk is None:
            raise RuntimeError("azure-cognitiveservices-speech is not installed")
        key = os.getenv("AZURE_SPEECH_KEY", "")
        region = os.getenv("AZURE_SPEECH_REGION", "")
        if not key or not region:
            raise RuntimeError("AZURE_SPEECH_KEY or AZURE_SPEECH_REGION is not configured")
        cfg = speechsdk.SpeechConfig(subscription=key, region=region)
        cfg.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        cached = cfg
    else:
        raise RuntimeError(f"Unsupported TTS provider: {provider}")
    _client_cache[provider] = cached
    return cached


def _synthesize(provider: str, text: str, role: str, language: str) -> tuple[bytes, str, str]:
    language_code, voice_name = _voice(provider, role, language)
    rate, pitch = _profile(role)
    if provider == "vertex":
        client = _client(provider)
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name),
            audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=rate, pitch=pitch),
        )
        return response.audio_content, voice_name, language_code
    if provider == "bedrock":
        client = _client(provider)
        ssml = f"<speak><prosody rate='{_rate_str(rate)}' pitch='{_pitch_str(pitch)}'>{text}</prosody></speak>"
        response = client.synthesize_speech(Engine=os.getenv("AWS_POLLY_ENGINE", "neural"), OutputFormat="mp3", Text=ssml, TextType="ssml", VoiceId=voice_name, LanguageCode=language_code)
        stream = response.get("AudioStream")
        if stream is None:
            raise RuntimeError("AWS Polly did not return audio stream")
        return stream.read(), voice_name, language_code
    cfg = _client(provider)
    ssml = f"<speak version='1.0' xml:lang='{language_code}'><voice name='{voice_name}'><prosody rate='{_rate_str(rate)}' pitch='{_pitch_str(pitch)}'>{text}</prosody></voice></speak>"
    result = speechsdk.SpeechSynthesizer(speech_config=cfg, audio_config=None).speak_ssml_async(ssml).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(result, "cancellation_details", None)
        raise RuntimeError(details.error_details if details else "Azure Speech synthesis failed")
    return bytes(result.audio_data), voice_name, language_code


def _list_voices(provider: str, language: str) -> list[dict]:
    if provider == "vertex":
        client = _client(provider)
        code, _ = _voice(provider, "expert", language)
        response = client.list_voices(request=texttospeech.ListVoicesRequest(language_code=code))
        return [{"name": v.name, "language_codes": list(v.language_codes), "ssml_gender": str(v.ssml_gender), "natural_sample_rate_hertz": v.natural_sample_rate_hertz} for v in response.voices]
    if provider == "bedrock":
        client = _client(provider)
        code, _ = _voice(provider, "expert", language)
        response = client.describe_voices(LanguageCode=code)
        return [{"name": v.get("Name", ""), "language_codes": [v.get("LanguageCode", "")], "ssml_gender": v.get("Gender", ""), "natural_sample_rate_hertz": None} for v in response.get("Voices", [])]
    code, name = _voice(provider, "expert", language)
    _client(provider)
    return [{"name": name, "language_codes": [code], "ssml_gender": "Unknown", "natural_sample_rate_hertz": 16000}]


@router.get("/provider")
async def get_tts_provider():
    return {"success": True, "tts_provider": _provider(), "ai_provider": os.getenv("AI_PROVIDER", "vertex"), "cloud": os.getenv("CLOUD_NAME", "unknown")}


@router.get("/voices")
async def list_voices(language: str = "zh-HK"):
    provider = _provider()
    try:
        voices = _list_voices(provider, language)
        return {"success": True, "provider": provider, "language": language, "voice_count": len(voices), "voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@router.get("/test")
async def test_tts(role: str = "scammer", language: str = "zh-HK", text: str = "你好，我係防詐專家，請注意防範詐騙。"):
    if role not in {"scammer", "victim", "expert"}:
        role = "expert"
    if language not in {"zh-HK", "zh-CN", "en-US", "ja-JP"}:
        language = "zh-HK"
    text = text.strip()[:200] or "你好，測試語音合成。"
    try:
        provider = _provider()
        audio, voice_name, language_code = _synthesize(provider, text, role, language)
        return FastAPIResponse(content=audio, media_type="audio/mpeg", headers={"X-Voice-Name": voice_name, "X-Language": language_code, "X-TTS-Provider": provider})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_tts(request: TTSRequest):
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text cannot be empty")
    text = text[:500]
    try:
        provider = _provider()
        audio, voice_name, _language_code = _synthesize(provider, text, request.role, request.language)
        return TTSResponse(success=True, audio_base64=base64.b64encode(audio).decode("utf-8"), role=request.role, voice_name=voice_name, language=request.language, provider=provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")
