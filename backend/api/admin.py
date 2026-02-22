"""
Battery Test Bench - Admin API
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial admin endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.calibration import Calibration, CalibrationCreate
from models.config import ConfigKey, ConfigUpdate
import aiosqlite
from config import settings
from datetime import date, timedelta
import json

router = APIRouter()


# Calibration Management

@router.get("/calibrations", response_model=List[Calibration])
async def get_all_calibrations():
    """Get calibration status for all stations"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM calibrations ORDER BY station_id") as cursor:
            rows = await cursor.fetchall()
            calibrations = []
            for row in rows:
                calibrations.append(Calibration(
                    id=row['id'],
                    station_id=row['station_id'],
                    calibration_date=date.fromisoformat(row['calibration_date']),
                    next_calibration_date=date.fromisoformat(row['next_calibration_date']),
                    calibrated_by=row['calibrated_by'],
                    notes=row['notes']
                ))
            return calibrations


@router.get("/calibrations/{station_id}", response_model=Calibration)
async def get_calibration(station_id: int):
    """Get calibration status for a specific station"""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM calibrations WHERE station_id = ?",
            (station_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"No calibration record for station {station_id}"
                )

            return Calibration(
                id=row['id'],
                station_id=row['station_id'],
                calibration_date=date.fromisoformat(row['calibration_date']),
                next_calibration_date=date.fromisoformat(row['next_calibration_date']),
                calibrated_by=row['calibrated_by'],
                notes=row['notes']
            )


@router.post("/calibrations", response_model=Calibration)
async def update_calibration(cal: CalibrationCreate):
    """Update calibration record for a station"""
    if not 1 <= cal.station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    next_cal_date = cal.next_calibration_date

    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Upsert calibration record
        await db.execute(
            """
            INSERT INTO calibrations (station_id, calibration_date, next_calibration_date, calibrated_by, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(station_id) DO UPDATE SET
                calibration_date = excluded.calibration_date,
                next_calibration_date = excluded.next_calibration_date,
                calibrated_by = excluded.calibrated_by,
                notes = excluded.notes
            """,
            (cal.station_id, cal.calibration_date, next_cal_date, cal.calibrated_by, cal.notes)
        )
        await db.commit()

        # Fetch and return updated record
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM calibrations WHERE station_id = ?",
            (cal.station_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return Calibration(
                id=row['id'],
                station_id=row['station_id'],
                calibration_date=date.fromisoformat(row['calibration_date']),
                next_calibration_date=date.fromisoformat(row['next_calibration_date']),
                calibrated_by=row['calibrated_by'],
                notes=row['notes']
            )


# Configuration Management

@router.get("/config", response_model=List[ConfigKey])
async def get_all_config():
    """Get all configuration keys"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM config ORDER BY key") as cursor:
            rows = await cursor.fetchall()
            return [ConfigKey(**dict(row)) for row in rows]


@router.get("/config/{key}", response_model=ConfigKey)
async def get_config(key: str):
    """Get a specific configuration value"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM config WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
            return ConfigKey(**dict(row))


@router.post("/config", response_model=ConfigKey)
async def set_config(update: ConfigUpdate):
    """Set a configuration value"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (update.key, update.value)
        )
        await db.commit()

        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM config WHERE key = ?", (update.key,)) as cursor:
            row = await cursor.fetchone()
            return ConfigKey(**dict(row))


@router.delete("/config/{key}")
async def delete_config(key: str):
    """Delete a configuration key"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        cursor = await db.execute("DELETE FROM config WHERE key = ?", (key,))
        await db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")

        return {"success": True, "message": f"Config key '{key}' deleted"}


# System Information

@router.get("/system/info")
async def system_info():
    """Get system information"""
    import platform
    import psutil

    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "app_version": settings.APP_VERSION
    }


@router.get("/system/health")
async def system_health():
    """Comprehensive system health check"""
    from services import i2c_poller, station_manager, data_logger

    health = {
        "overall": "healthy",
        "services": {}
    }

    # Check I2C poller
    try:
        i2c_status = await i2c_poller.get_status()
        health["services"]["i2c_poller"] = {
            "status": "healthy" if i2c_status["running"] else "stopped",
            "last_poll": i2c_status.get("last_poll")
        }
    except Exception as e:
        health["services"]["i2c_poller"] = {"status": "error", "error": str(e)}
        health["overall"] = "degraded"

    # Check InfluxDB
    try:
        influx_status = await data_logger.check_influxdb_connection()
        health["services"]["influxdb"] = {
            "status": "healthy" if influx_status else "disconnected"
        }
        if not influx_status:
            health["overall"] = "degraded"
    except Exception as e:
        health["services"]["influxdb"] = {"status": "error", "error": str(e)}
        health["overall"] = "degraded"

    # Check SQLite
    try:
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            await db.execute("SELECT 1")
        health["services"]["sqlite"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["sqlite"] = {"status": "error", "error": str(e)}
        health["overall"] = "degraded"

    return health
