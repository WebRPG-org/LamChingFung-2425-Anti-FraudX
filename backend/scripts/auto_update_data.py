"""
自動化數據更新腳本
定期運行 scraper 並更新 RAG 數據庫
"""

import os
import sys
import time
import schedule
from datetime import datetime
from pathlib import Path

# 添加 backend 到路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.logger import log


def run_scraper():
    """運行 scraper 抓取最新數據"""
    log.info("=" * 60)
    log.info(f"[自動更新] 開始運行 scraper - {datetime.now()}")
    log.info("=" * 60)
    
    try:
        # 運行 scraper
        import scripts.scraper as scraper
        scraper.main()
        log.info("[自動更新] ✅ Scraper 運行成功")
        return True
    except Exception as e:
        log.error(f"[自動更新] ❌ Scraper 運行失敗: {e}")
        return False


def rebuild_rag_db():
    """重建 RAG 數據庫"""
    log.info("=" * 60)
    log.info(f"[自動更新] 開始重建 RAG 數據庫 - {datetime.now()}")
    log.info("=" * 60)
    
    try:
        from services.rag_service import build_and_persist_db
        build_and_persist_db()
        log.info("[自動更新] ✅ RAG 數據庫重建成功")
        return True
    except Exception as e:
        log.error(f"[自動更新] ❌ RAG 數據庫重建失敗: {e}")
        return False


def update_lite_versions():
    """更新精簡版數據"""
    log.info("=" * 60)
    log.info(f"[自動更新] 開始更新精簡版數據 - {datetime.now()}")
    log.info("=" * 60)
    
    try:
        # 運行精簡版創建腳本
        import subprocess
        
        # 創建 lite 版本
        result = subprocess.run(
            [sys.executable, "scripts/create_lite_data.py"],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            log.info("[自動更新] ✅ Lite 版本創建成功")
        else:
            log.error(f"[自動更新] ❌ Lite 版本創建失敗: {result.stderr}")
            return False
        
        # 創建 ultra lite 版本
        result = subprocess.run(
            [sys.executable, "scripts/create_ultra_lite_data.py"],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            log.info("[自動更新] ✅ Ultra Lite 版本創建成功")
        else:
            log.error(f"[自動更新] ❌ Ultra Lite 版本創建失敗: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        log.error(f"[自動更新] ❌ 精簡版數據更新失敗: {e}")
        return False


def full_update_cycle():
    """完整的更新週期"""
    log.info("\n" + "=" * 60)
    log.info("🔄 開始完整更新週期")
    log.info("=" * 60)
    
    # 步驟 1: 運行 scraper
    if not run_scraper():
        log.error("❌ 更新週期失敗：Scraper 運行失敗")
        return False
    
    # 步驟 2: 更新精簡版數據
    if not update_lite_versions():
        log.warning("⚠️ 精簡版數據更新失敗，但繼續進行")
    
    # 步驟 3: 重建 RAG 數據庫
    if not rebuild_rag_db():
        log.error("❌ 更新週期失敗：RAG 數據庫重建失敗")
        return False
    
    log.info("\n" + "=" * 60)
    log.info("✅ 完整更新週期成功完成")
    log.info("=" * 60 + "\n")
    return True


def run_scheduler(interval_days: int = 3):
    """
    運行定時任務調度器
    
    Args:
        interval_days: 更新間隔（天數），默認 3 天
    """
    log.info("=" * 60)
    log.info("🚀 自動化數據更新調度器啟動")
    log.info("=" * 60)
    log.info(f"更新間隔: 每 {interval_days} 天")
    log.info(f"下次更新時間: {interval_days} 天後")
    log.info("=" * 60 + "\n")
    
    # 立即運行一次
    log.info("🔄 執行首次更新...")
    full_update_cycle()
    
    # 設置定時任務
    schedule.every(interval_days).days.do(full_update_cycle)
    
    # 持續運行
    try:
        while True:
            schedule.run_pending()
            time.sleep(3600)  # 每小時檢查一次
    except KeyboardInterrupt:
        log.info("\n⏹️ 調度器已停止")


def run_once():
    """運行一次完整更新"""
    log.info("🔄 運行單次更新...")
    success = full_update_cycle()
    
    if success:
        log.info("\n✅ 單次更新完成")
    else:
        log.error("\n❌ 單次更新失敗")
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自動化數據更新工具")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule"],
        default="once",
        help="運行模式：once=單次更新, schedule=定時調度"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="定時調度間隔（天數），默認 3 天"
    )
    
    args = parser.parse_args()
    
    if args.mode == "once":
        run_once()
    else:
        run_scheduler(interval_days=args.interval)
