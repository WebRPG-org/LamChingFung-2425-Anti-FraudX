"""
Seed `scraped_alerts.json` into the configured database.
"""

from __future__ import annotations

import json
from pathlib import Path

from utils.db import execute, fetchone, initialize_game_tables, is_postgres, placeholder

ROOT_DIR = Path(__file__).resolve().parents[1]
ALERTS_PATH = ROOT_DIR / "backend" / "data" / "scraped_alerts.json"


def seed_alerts() -> int:
    initialize_game_tables()
    existing = fetchone("SELECT COUNT(*) FROM scam_alerts")
    existing_count = existing[0] if existing else 0
    if existing_count:
        return existing_count

    rows = json.loads(ALERTS_PATH.read_text(encoding="utf-8"))
    ph = placeholder()
    query = (
        f"INSERT INTO scam_alerts (title, published_date, link, source, content) "
        f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph})"
    )
    for row in rows:
        execute(
            query,
            [
                row.get("title", ""),
                row.get("date", ""),
                row.get("link", ""),
                row.get("source", ""),
                row.get("content", ""),
            ],
        )
    return len(rows)


if __name__ == "__main__":
    count = seed_alerts()
    print(f"seeded_alerts={count}")
