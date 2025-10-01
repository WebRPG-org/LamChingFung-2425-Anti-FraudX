from ..core.celery_app import celery_app
from .sfc_alertlist_scraper import scrape_and_store_sfc_alerts_sync
from .data_ingestor import sync_hkma_scam_reports, sync_official_contacts
from celery.schedules import crontab
import asyncio

@celery_app.task(name="ingestion.scrape_sfc")
def scrape_sfc_task():
    print("Celery Worker 正在執行同步的 SFC 爬蟲任務...")
    scrape_and_store_sfc_alerts_sync()
    print("SFC 爬蟲任務執行完畢。")

@celery_app.task(name="ingestion.sync_hkma_scams")
def sync_hkma_scams_task():
    print("Celery Worker 正在執行 HKMA 詐騙新聞稿同步任務...")
    asyncio.run(sync_hkma_scam_reports())
    print("HKMA 詐騙新聞稿同步任務執行完畢。")
    
@celery_app.task(name="ingestion.sync_official_data")
def sync_official_data_task():
    print("Celery Worker 正在執行官方聯絡方式與公司同步任務...")
    asyncio.run(sync_official_contacts())
    print("官方聯絡方式與公司同步任務執行完畢。")

# --- 設定所有定時任務 ---
celery_app.conf.beat_schedule = {
    # 每日凌晨 3 點執行高頻更新
    'daily-high-frequency-sync': {
        'task': 'ingestion.scrape_sfc',
        'schedule': crontab(hour=3, minute=3),
    },
    'daily-hkma-scams-sync': {
        'task': 'ingestion.sync_hkma_scams',
        'schedule': crontab(hour=3, minute=15),
    },
    # 每週日凌晨 4 點執行低頻更新
    'weekly-low-frequency-sync': {
        'task': 'ingestion.sync_official_data',
        'schedule': crontab(hour=4, minute=0, day_of_week='sun'),
    },
}

# --- 簡單的加法任務，用於測試 Celery ---
@celery_app.task(name="tasks.add")
def add(x, y):
    result = x + y
    print(f"--- [Celery Task Executed] 'add': {x} + {y} = {result} ---")
    return result
