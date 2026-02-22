"""
Battery Test Bench - Data Logger Service
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Added periodic chart_data write to job_tasks.chart_data
                      alongside existing InfluxDB logging (SQLite backup for
                      offline/report use)
v1.0.1 (2026-02-12): Initial data logger with InfluxDB
"""

import asyncio
import json
import logging
from typing import List, Optional
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from config import settings
from services import i2c_poller, psu_controller
from models.session import SessionSummary, SessionDetail, SessionData, SessionStatus
import aiosqlite

logger = logging.getLogger(__name__)


class DataLogger:
    """Logs station data to InfluxDB"""

    def __init__(self):
        self.client = None
        self.write_api = None
        self.queue = asyncio.Queue(maxsize=settings.LOG_QUEUE_SIZE)

    async def start_logger(self):
        """Start data logger loop"""
        logger.info("Starting data logger")

        # Initialize InfluxDB client
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
            logger.info("InfluxDB client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            # Continue running but log locally only
            pass

        while True:
            await self._log_all_stations()
            await asyncio.sleep(settings.I2C_POLL_INTERVAL)

    async def _log_all_stations(self):
        """Log data from all stations to InfluxDB"""
        for station_id in range(1, 13):
            try:
                i2c_data = i2c_poller.get_station_data(station_id)
                if not i2c_data:
                    continue

                # Get V/I readings
                voltage_mv = await psu_controller.read_voltage(station_id)
                current_ma = await psu_controller.read_current(station_id)
                temperature_c = i2c_data.get("temperature_c")

                if temperature_c is None:
                    continue  # Don't log without temperature

                # Create InfluxDB point
                point = (
                    Point("station_data")
                    .tag("station_id", str(station_id))
                    .field("voltage_mv", voltage_mv or 0)
                    .field("current_ma", current_ma or 0)
                    .field("temperature_c", temperature_c)
                    .time(datetime.utcnow())
                )

                # Write to InfluxDB
                if self.write_api:
                    self.write_api.write(
                        bucket=settings.INFLUXDB_BUCKET,
                        record=point
                    )

            except Exception as e:
                logger.error(f"Failed to log station {station_id}: {e}")

    async def _write_chart_data_to_job_tasks(self):
        """
        Periodic backup: write sampled V/I/T data to active job_tasks.chart_data.
        Called alongside InfluxDB logging to ensure offline/report availability.
        This supplements the per-step monitoring in task_orchestrator.
        """
        try:
            async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT jt.id, jt.chart_data, wj.station_id
                    FROM job_tasks jt
                    JOIN work_jobs wj ON jt.work_job_id = wj.id
                    WHERE jt.status = 'in_progress' AND jt.is_automated = 1
                """)
                active_tasks = await cursor.fetchall()

                for task in active_tasks:
                    station_id = task["station_id"]
                    i2c_data = i2c_poller.get_station_data(station_id)
                    if not i2c_data:
                        continue

                    voltage_mv = await psu_controller.read_voltage(station_id)
                    current_ma = await psu_controller.read_current(station_id)
                    temp_c = i2c_data.get("temperature_c", 0)

                    chart_data = json.loads(task["chart_data"] or "[]")
                    last_t = chart_data[-1]["t"] if chart_data else 0
                    chart_data.append({
                        "t": last_t + int(settings.I2C_POLL_INTERVAL),
                        "V": voltage_mv or 0,
                        "I": current_ma or 0,
                        "T": round(temp_c, 1) if temp_c else 0,
                    })

                    await db.execute("""
                        UPDATE job_tasks SET chart_data = ?, data_points = ?
                        WHERE id = ?
                    """, (json.dumps(chart_data), len(chart_data), task["id"]))

                if active_tasks:
                    await db.commit()

        except Exception as e:
            logger.debug(f"chart_data backup write failed: {e}")

    async def check_influxdb_connection(self) -> bool:
        """Check if InfluxDB is accessible"""
        if not self.client:
            return False

        try:
            health = self.client.health()
            return health.status == "pass"
        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return False

    async def get_sessions(
        self,
        station_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SessionSummary]:
        """Query sessions from SQLite"""
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if station_id:
            query += " AND station_id = ?"
            params.append(station_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND start_time <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                sessions = []
                for row in rows:
                    duration_s = None
                    if row['end_time']:
                        start = datetime.fromisoformat(row['start_time'])
                        end = datetime.fromisoformat(row['end_time'])
                        duration_s = int((end - start).total_seconds())

                    sessions.append(SessionSummary(
                        id=row['id'],
                        station_id=row['station_id'],
                        recipe_name=row.get('recipe_name'),
                        start_time=datetime.fromisoformat(row['start_time']),
                        end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                        status=SessionStatus(row['status']),
                        battery_serial=row.get('battery_serial'),
                        duration_s=duration_s,
                        efficiency_percent=None  # TODO: Calculate from InfluxDB
                    ))
                return sessions

    async def get_session_detail(self, session_id: int) -> Optional[SessionDetail]:
        """Get detailed session with time-series data from InfluxDB"""
        # TODO: Implement InfluxDB query for time-series data
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                # Stub implementation - return session without data points
                return SessionDetail(
                    id=row['id'],
                    station_id=row['station_id'],
                    recipe_id=row['recipe_id'],
                    recipe_name=None,
                    start_time=datetime.fromisoformat(row['start_time']),
                    end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                    status=SessionStatus(row['status']),
                    battery_serial=row.get('battery_serial'),
                    notes=row.get('notes'),
                    data_points=[]  # TODO: Query from InfluxDB
                )

    async def export_session_csv(self, session_id: int) -> Optional[str]:
        """Export session data as CSV"""
        # TODO: Implement CSV export
        return None


# Singleton instance
_logger = DataLogger()


async def start_logger():
    """Start the data logger"""
    await _logger.start_logger()


async def check_influxdb_connection() -> bool:
    """Check InfluxDB"""
    return await _logger.check_influxdb_connection()


async def get_sessions(*args, **kwargs) -> List[SessionSummary]:
    """Get sessions"""
    return await _logger.get_sessions(*args, **kwargs)


async def get_session_detail(session_id: int) -> Optional[SessionDetail]:
    """Get session detail"""
    return await _logger.get_session_detail(session_id)


async def export_session_csv(session_id: int) -> Optional[str]:
    """Export CSV"""
    return await _logger.export_session_csv(session_id)
