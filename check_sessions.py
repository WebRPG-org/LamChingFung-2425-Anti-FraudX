#!/usr/bin/env python3
"""檢查 anti_fraud_game.db 中的 session 資料"""

import sqlite3
import os

DATABASE_PATH = "anti_fraud_game.db"

if not os.path.exists(DATABASE_PATH):
    print(f"❌ 資料庫不存在: {DATABASE_PATH}")
    exit(1)

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# 查詢最新的 5 筆 sessions
print("=" * 80)
print("📊 最新的 5 筆 Sessions:")
print("=" * 80)
cursor.execute("SELECT id, persona_type, created_at, status FROM sessions ORDER BY created_at DESC LIMIT 5")
sessions = cursor.fetchall()

if not sessions:
    print("⚠️  資料庫中沒有任何 session 記錄")
else:
    for i, session in enumerate(sessions, 1):
        print(f"\n{i}. Session ID: {session[0]}")
        print(f"   Persona Type: {session[1]}")
        print(f"   Created At: {session[2]}")
        print(f"   Status: {session[3]}")

# 統計總數
cursor.execute("SELECT COUNT(*) FROM sessions")
total = cursor.fetchone()[0]
print(f"\n{'=' * 80}")
print(f"📈 總共有 {total} 筆 session 記錄")
print("=" * 80)

conn.close()
