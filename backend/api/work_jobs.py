"""
Battery Test Bench - Work Jobs API
Version: 1.0.0

Changelog:
v1.0.0 (2026-02-22): Read-only router with filters
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from database import get_db, execute_one, execute_all

router = APIRouter(prefix="/work-jobs", tags=["work-jobs"])


@router.get("/")
async def list_work_jobs(
    work_order_id: Optional[int] = None,
    station_id: Optional[int] = None,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    search: Optional[str] = None,
):
    """List work jobs with optional filters."""
    async with get_db() as db:
        query = """
            SELECT wj.*,
                   wo.customer_id,
                   c.name AS customer_name
            FROM work_jobs wj
            LEFT JOIN work_orders wo ON wj.work_order_id = wo.id
            LEFT JOIN customers c ON wo.customer_id = c.id
        """
        conditions = []
        params: list = []

        if work_order_id is not None:
            conditions.append("wj.work_order_id = ?")
            params.append(work_order_id)
        if station_id is not None:
            conditions.append("wj.station_id = ?")
            params.append(station_id)
        if status:
            conditions.append("wj.status = ?")
            params.append(status)
        if customer_id is not None:
            conditions.append("wo.customer_id = ?")
            params.append(customer_id)
        if from_date:
            conditions.append("wj.started_at >= ?")
            params.append(from_date)
        if to_date:
            conditions.append("wj.started_at <= ?")
            params.append(to_date)
        if search:
            conditions.append(
                "(wj.work_order_number LIKE ? OR wj.battery_serial LIKE ? "
                "OR wj.battery_part_number LIKE ? OR c.name LIKE ?)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY wj.id DESC LIMIT 200"

        rows = await execute_all(db, query, params)
        return rows


@router.get("/{job_id}")
async def get_work_job(job_id: int):
    """Get single work job."""
    async with get_db() as db:
        row = await execute_one(db, """
            SELECT wj.*,
                   wo.customer_id,
                   c.name AS customer_name
            FROM work_jobs wj
            LEFT JOIN work_orders wo ON wj.work_order_id = wo.id
            LEFT JOIN customers c ON wo.customer_id = c.id
            WHERE wj.id = ?
        """, (job_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Work job not found")
        return row
