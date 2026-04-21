"""
Database helpers for SQLite/Postgres dual support.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover
    psycopg2 = None
    RealDictCursor = None

ROOT_DIR = Path(__file__).resolve().parents[2]
SQLITE_PATH = ROOT_DIR / "anti_fraud_game.db"
DEFAULT_DATABASE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def is_postgres() -> bool:
    return get_database_url().startswith("postgres")


def placeholder() -> str:
    return "%s" if is_postgres() else "?"


@contextmanager
def get_connection():
    database_url = get_database_url()

    if database_url.startswith("postgres"):
        if psycopg2 is None:
            raise RuntimeError("psycopg2 is required for PostgreSQL support")
        conn = psycopg2.connect(database_url)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
        return

    conn = sqlite3.connect(str(SQLITE_PATH))
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def fetchone(query: str, params: Optional[Iterable[Any]] = None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params or []))
        return cur.fetchone()


def fetchall(query: str, params: Optional[Iterable[Any]] = None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params or []))
        return cur.fetchall()


def execute(query: str, params: Optional[Iterable[Any]] = None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params or []))


def initialize_game_tables():
    with get_connection() as conn:
        cur = conn.cursor()
        if is_postgres():
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    persona_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scam_alerts (
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    published_date TEXT,
                    link TEXT,
                    source TEXT,
                    content TEXT NOT NULL
                )
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    persona_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scam_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    published_date TEXT,
                    link TEXT,
                    source TEXT,
                    content TEXT NOT NULL
                )
                """
            )
