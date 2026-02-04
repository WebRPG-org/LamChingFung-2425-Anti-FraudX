"""
Prompt 版本管理 API 路由
提供版本控制、A/B 測試等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from utils.prompt_version_manager import PromptVersionManager
from utils.logger import log

router = APIRouter(prefix="/api/prompt-versions", tags=["Prompt Version Management"])

# 全局版本管理器實例
version_manager = PromptVersionManager()


# ==================== Pydantic Models ====================

class PromptVersionCreate(BaseModel):
    """創建新版本的請求模型"""
    version: str
    prompt: str
    metadata: Dict
    agent_type: str


class SetActiveVersionRequest(BaseModel):
    """設置活躍版本的請求模型"""
    version: str


class ABTestRequest(BaseModel):
    """A/B 測試請求模型"""
    agent_type: str
    version_a: str
    version_b: str
    sample_size: int = 10


# ==================== API Endpoints ====================

@router.get("/{agent_type}")
async def list_prompt_versions(agent_type: str):
    """
    列出指定 Agent 類型的所有 Prompt 版本
    
    Args:
        agent_type: Agent 類型 (expert, scammer, victim)
        
    Returns:
        版本列表及其統計信息
    """
    try:
        log.info(f"📋 列出 Prompt 版本: {agent_type}")
        
        versions = version_manager.list_versions(agent_type)
        
        if not versions:
            return {
                "agent_type": agent_type,
                "versions": [],
                "message": "尚未註冊任何版本"
            }
        
        return {
            "agent_type": agent_type,
            "versions": versions,
            "total_count": len(versions)
        }
        
    except Exception as e:
        log.error(f"❌ 列出版本失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_type}")
async def create_prompt_version(agent_type: str, request: PromptVersionCreate):
    """
    創建新的 Prompt 版本
    
    Args:
        agent_type: Agent 類型
        request: 版本創建請求
        
    Returns:
        創建結果
    """
    try:
        log.info(f"📝 創建新版本: {agent_type}/{request.version}")
        
        # 檢查版本是否已存在
        existing = version_manager.get_version(agent_type, request.version)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"版本 {request.version} 已存在"
            )
        
        # 註冊新版本
        version_manager.register_version(
            version=request.version,
            prompt=request.prompt,
            metadata=request.metadata,
            agent_type=agent_type
        )
        
        return {
            "status": "success",
            "agent_type": agent_type,
            "version": request.version,
            "message": f"版本 {request.version} 創建成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"❌ 創建版本失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_type}/{version}")
async def get_prompt_version(agent_type: str, version: str):
    """
    獲取指定版本的 Prompt 內容
    
    Args:
        agent_type: Agent 類型
        version: 版本號
        
    Returns:
        Prompt 內容
    """
    try:
        log.info(f"📖 獲取版本: {agent_type}/{version}")
        
        prompt = version_manager.get_version(agent_type, version)
        
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"版本 {agent_type}/{version} 不存在"
            )
        
        return {
            "agent_type": agent_type,
            "version": version,
            "prompt": prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"❌ 獲取版本失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_type}/active")
async def set_active_version(agent_type: str, request: SetActiveVersionRequest):
    """
    設置活躍版本（版本回退功能）
    
    Args:
        agent_type: Agent 類型
        request: 包含要設置的版本號
        
    Returns:
        設置結果
    """
    try:
        log.info(f"🔄 設置活躍版本: {agent_type}/{request.version}")
        
        # 檢查版本是否存在
        prompt = version_manager.get_version(agent_type, request.version)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"版本 {agent_type}/{request.version} 不存在"
            )
        
        # 設置活躍版本
        version_manager.set_active_version(agent_type, request.version)
        
        return {
            "status": "success",
            "agent_type": agent_type,
            "active_version": request.version,
            "message": f"已切換到版本 {request.version}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"❌ 設置活躍版本失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_type}/active/current")
async def get_active_version(agent_type: str):
    """
    獲取當前活躍版本
    
    Args:
        agent_type: Agent 類型
        
    Returns:
        當前活躍版本號
    """
    try:
        active_version = version_manager.get_active_version(agent_type)
        
        return {
            "agent_type": agent_type,
            "active_version": active_version
        }
        
    except Exception as e:
        log.error(f"❌ 獲取活躍版本失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_type}/best")
async def get_best_version(agent_type: str):
    """
    獲取性能最佳的版本
    
    Args:
        agent_type: Agent 類型
        
    Returns:
        最佳版本號及其統計信息
    """
    try:
        log.info(f"🏆 獲取最佳版本: {agent_type}")
        
        best_version = version_manager.get_best_version(agent_type)
        
        if not best_version:
            return {
                "agent_type": agent_type,
                "best_version": None,
                "message": "數據不足，無法判定最佳版本（需要至少 5 次使用記錄）"
            }
        
        # 獲取最佳版本的詳細信息
        versions = version_manager.list_versions(agent_type)
        best_info = next((v for v in versions if v["version"] == best_version), None)
        
        return {
            "agent_type": agent_type,
            "best_version": best_version,
            "details": best_info
        }
        
    except Exception as e:
        log.error(f"❌ 獲取最佳版本失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test")
async def run_ab_test(request: ABTestRequest):
    """
    運行 A/B 測試
    
    Args:
        request: A/B 測試請求
        
    Returns:
        測試結果和分析
    """
    try:
        log.info(f"🧪 運行 A/B 測試: {request.agent_type} - {request.version_a} vs {request.version_b}")
        
        # 檢查版本是否存在
        version_a_prompt = version_manager.get_version(request.agent_type, request.version_a)
        version_b_prompt = version_manager.get_version(request.agent_type, request.version_b)
        
        if not version_a_prompt:
            raise HTTPException(
                status_code=404,
                detail=f"版本 {request.version_a} 不存在"
            )
        
        if not version_b_prompt:
            raise HTTPException(
                status_code=404,
                detail=f"版本 {request.version_b} 不存在"
            )
        
        # 運行 A/B 測試
        results = version_manager.ab_test(
            agent_type=request.agent_type,
            version_a=request.version_a,
            version_b=request.version_b,
            sample_size=request.sample_size
        )
        
        return {
            "status": "success",
            "agent_type": request.agent_type,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"❌ A/B 測試失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_type}/{version}")
async def delete_prompt_version(agent_type: str, version: str):
    """
    刪除指定版本（預留接口，暫不實現）
    
    Args:
        agent_type: Agent 類型
        version: 版本號
        
    Returns:
        刪除結果
    """
    # 暫不實現刪除功能，避免誤刪重要版本
    raise HTTPException(
        status_code=501,
        detail="刪除功能暫未實現，請使用版本回退功能"
    )


@router.get("/")
async def get_all_versions():
    """
    獲取所有 Agent 類型的版本概覽
    
    Returns:
        所有版本的概覽信息
    """
    try:
        log.info("📊 獲取所有版本概覽")
        
        overview = {}
        for agent_type in ["expert", "scammer", "victim"]:
            versions = version_manager.list_versions(agent_type)
            active_version = version_manager.get_active_version(agent_type)
            best_version = version_manager.get_best_version(agent_type)
            
            overview[agent_type] = {
                "total_versions": len(versions),
                "active_version": active_version,
                "best_version": best_version,
                "versions": versions
            }
        
        return {
            "status": "success",
            "overview": overview
        }
        
    except Exception as e:
        log.error(f"❌ 獲取版本概覽失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
