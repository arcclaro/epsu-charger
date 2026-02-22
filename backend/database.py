"""
Battery Test Bench - Database Connection Manager
Version: 1.0.0

Changelog:
v1.0.0 (2026-02-18): Initial database connection manager with async helpers

Provides centralized async SQLite connection management for all endpoints.
Uses aiosqlite with WAL journal mode and foreign key enforcement.
"""

import os
import json
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

_db_path: str = None


def get_db_path() -> str:
    """Resolve database path, create data directory if needed"""
    global _db_path
    if _db_path is None:
        _db_path = os.environ.get(
            "BATTERY_BENCH_DB",
            str(Path(__file__).parent / "data" / "battery_bench.db")
        )
        os.makedirs(os.path.dirname(os.path.abspath(_db_path)), exist_ok=True)
    return _db_path


@asynccontextmanager
async def get_db():
    """Async context manager yielding an aiosqlite connection with WAL + FK"""
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        await db.close()


async def execute_one(db, sql: str, params=()) -> dict | None:
    """Execute query and return first row as dict, or None"""
    cursor = await db.execute(sql, params)
    row = await cursor.fetchone()
    return dict(row) if row else None


async def execute_all(db, sql: str, params=()) -> list[dict]:
    """Execute query and return all rows as list of dicts"""
    cursor = await db.execute(sql, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def execute_insert(db, sql: str, params=()) -> int:
    """Execute INSERT, commit, and return lastrowid"""
    cursor = await db.execute(sql, params)
    await db.commit()
    return cursor.lastrowid


async def execute_update(db, sql: str, params=()) -> int:
    """Execute UPDATE/DELETE, commit, and return rowcount"""
    cursor = await db.execute(sql, params)
    await db.commit()
    return cursor.rowcount


def json_col(data) -> str:
    """Serialize Python object to JSON TEXT for SQLite storage"""
    if data is None:
        return '[]'
    return json.dumps(data, default=str)


def from_json(text: str):
    """Deserialize JSON TEXT column to Python object"""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
