"""
Battery Test Bench - Job Tasks API
Version: 2.0.0

Submit manual task results, query task status, tool selection/validation.
Supports the PWA workflow for manual test data entry.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import aiosqlite
import logging

from config import settings
from services import task_orchestrator, tool_validator

router = APIRouter(prefix="/job-tasks", tags=["job-tasks"])
logger = logging.getLogger(__name__)


class ManualResultSubmit(BaseModel):
    """Submit manual task results from PWA."""
    measured_values: Dict[str, Any] = {}
    step_result: str  # 'pass', 'fail', 'info'
    result_notes: str = ""
    performed_by: str = ""
    tool_ids: Optional[List[int]] = None


class StartJobRequest(BaseModel):
    """Start a job with procedure resolution."""
    work_order_item_id: int
    station_id: int
    service_type: str = "capacity_test"
    months_since_service: int = 0
    started_by: str = ""


@router.get("/job/{work_job_id}")
async def get_job_tasks(work_job_id: int):
    """Get all tasks for a work job."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT jt.*, ps.measurement_key, ps.measurement_unit,
                   ps.pass_criteria_type, ps.pass_criteria_value
            FROM job_tasks jt
            LEFT JOIN procedure_steps ps ON jt.step_id = ps.id
            WHERE jt.work_job_id = ?
            ORDER BY jt.task_number ASC
        """, (work_job_id,))
        rows = await cursor.fetchall()

        tasks = []
        for r in rows:
            d = dict(r)
            d["params"] = json.loads(d.get("params") or "{}")
            d["measured_values"] = json.loads(d.get("measured_values") or "{}")
            d["chart_data"] = json.loads(d.get("chart_data") or "[]")
            tasks.append(d)
        return tasks


@router.get("/{task_id}")
async def get_task(task_id: int):
    """Get a single task with full details."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM job_tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        d = dict(row)
        d["params"] = json.loads(d.get("params") or "{}")
        d["measured_values"] = json.loads(d.get("measured_values") or "{}")

        # Get tool usage for this task
        cursor = await db.execute("""
            SELECT * FROM task_tool_usage WHERE job_task_id = ?
        """, (task_id,))
        d["tools_used"] = [dict(t) for t in await cursor.fetchall()]

        return d


@router.post("/{task_id}/submit")
async def submit_manual_result(task_id: int, data: ManualResultSubmit):
    """
    Submit manual task results from PWA form.
    Validates tools, records tool usage, updates task.
    """
    # Validate and record tool usage
    if data.tool_ids:
        for tool_id in data.tool_ids:
            try:
                await tool_validator.record_tool_usage(task_id, tool_id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    # Submit result
    await task_orchestrator.submit_manual_result(
        job_task_id=task_id,
        measured_values=data.measured_values,
        step_result=data.step_result,
        result_notes=data.result_notes,
        performed_by=data.performed_by,
    )

    return {"success": True, "message": f"Task {task_id} result submitted"}


@router.post("/{task_id}/skip")
async def skip_task(task_id: int, reason: str = ""):
    """Skip a manual task (mark as skipped)."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        await db.execute("""
            UPDATE job_tasks SET status = 'skipped', step_result = 'skipped',
                   result_notes = ?
            WHERE id = ? AND status IN ('pending', 'awaiting_input')
        """, (reason, task_id))
        await db.commit()
    return {"success": True, "message": f"Task {task_id} skipped"}


@router.get("/awaiting-input/{station_id}")
async def get_awaiting_tasks(station_id: int):
    """Get tasks awaiting manual input for a station."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT jt.* FROM job_tasks jt
            JOIN work_jobs wj ON jt.work_job_id = wj.id
            WHERE wj.station_id = ? AND jt.status = 'awaiting_input'
            ORDER BY jt.task_number ASC
        """, (station_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/start-job")
async def start_job(data: StartJobRequest):
    """
    Start a new job with full procedure resolution.
    Creates work_job, resolves procedure, creates job_tasks, starts orchestrator.
    """
    from services.procedure_resolver import ProcedureResolver
    from services.job_task_factory import JobTaskFactory

    try:
        # Resolve procedure
        resolver = ProcedureResolver()
        procedure = await resolver.resolve_procedure(
            data.work_order_item_id, data.service_type,
            data.months_since_service)

        # Create work_job
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Get item details
            cursor = await db.execute("""
                SELECT woi.*, wo.work_order_number, wo.id as wo_id
                FROM work_order_items woi
                JOIN work_orders wo ON woi.work_order_id = wo.id
                WHERE woi.id = ?
            """, (data.work_order_item_id,))
            item = await cursor.fetchone()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")

            cursor = await db.execute("""
                INSERT INTO work_jobs
                    (work_order_id, work_order_item_id, work_order_number,
                     battery_serial, battery_part_number, battery_amendment,
                     tech_pub_id, tech_pub_cmm, tech_pub_revision,
                     station_id, status, started_at, started_by,
                     profile_id, procedure_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'),
                        ?, ?, ?)
            """, (
                item["wo_id"], data.work_order_item_id,
                item["work_order_number"],
                item["serial_number"], item["part_number"],
                item["amendment"],
                procedure.tech_pub_id, procedure.cmm_number,
                procedure.cmm_revision,
                data.station_id, data.started_by,
                procedure.profile_id,
                json.dumps({
                    "cmm": procedure.cmm_number,
                    "sections": len(procedure.sections),
                    "steps": procedure.total_steps,
                }),
            ))
            work_job_id = cursor.lastrowid
            await db.commit()

        # Create job_tasks from resolved procedure
        factory = JobTaskFactory()
        task_ids = await factory.create_tasks_for_job(work_job_id, procedure)

        # Start orchestrator
        await task_orchestrator.execute_job(work_job_id, data.station_id)

        return {
            "work_job_id": work_job_id,
            "tasks_created": len(task_ids),
            "estimated_hours": round(procedure.estimated_total_hours, 1),
            "cmm": procedure.cmm_number,
            "message": f"Job started with {len(task_ids)} tasks"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/available")
async def get_available_tools(category: Optional[str] = None):
    """Get available calibrated tools, optionally filtered by category."""
    tools = await tool_validator.get_available_tools(category)
    return tools
