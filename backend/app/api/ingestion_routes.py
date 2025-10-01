from fastapi import APIRouter
from ..ingestion.tasks import (
    scrape_sfc_task,
    sync_hkma_scams_task,
    sync_official_data_task
)

router = APIRouter()

@router.post("/ingestion/trigger-sfc-scrape", tags=["Ingestion"])
def trigger_sfc_scrape():
    """手動觸發 SFC 警示名單的爬蟲任務。"""
    task = scrape_sfc_task.delay()
    return {"message": "SFC 警示名單爬蟲任務已觸發。", "task_id": task.id}

@router.post("/ingestion/trigger-hkma-scams", tags=["Ingestion"])
def trigger_hkma_scams():
    """手動觸發 HKMA 詐騙新聞稿的同步任務。"""
    task = sync_hkma_scams_task.delay()
    return {"message": "HKMA 詐騙新聞稿同步任務已觸發。", "task_id": task.id}

@router.post("/ingestion/trigger-official-data", tags=["Ingestion"])
def trigger_official_data():
    """手動觸發官方聯絡方式與公司的同步任務。"""
    task = sync_official_data_task.delay()
    return {"message": "官方聯絡方式與公司同步任務已觸發。", "task_id": task.id}

