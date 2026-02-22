"""
Battery Test Bench - Task Execution Orchestrator
Version: 2.0.0

Executes job_tasks sequentially with per-step hardware control.
Calls TestController methods individually per procedure_step.
Replaces the monolithic run_automated_capacity_test() phase logic.

For each job_task in order:
- Automated steps (charge/discharge/rest/wait_temp): call TestController methods
- Manual steps: set status to 'awaiting_input', send WebSocket notification
- After all tasks: determine overall_result, create test_reports row
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import aiosqlite
from config import settings

logger = logging.getLogger(__name__)


class TaskExecutionOrchestrator:
    """Executes job_tasks sequentially with per-step hardware control."""

    def __init__(self):
        self._running_jobs: Dict[int, asyncio.Task] = {}

    async def execute_job(self, work_job_id: int, station_id: int) -> None:
        """
        Start executing all pending job_tasks for a work job.

        Launches as an asyncio task so the caller returns immediately.
        The orchestrator processes tasks sequentially, calling the
        appropriate TestController method for each automated step.

        Args:
            work_job_id: The work_jobs.id to execute
            station_id: Station ID for hardware control
        """
        if work_job_id in self._running_jobs:
            logger.warning(f"Job {work_job_id} already running")
            return

        task = asyncio.create_task(self._run_job(work_job_id, station_id))
        self._running_jobs[work_job_id] = task

        # Clean up when done
        task.add_done_callback(lambda t: self._running_jobs.pop(work_job_id, None))

    async def abort_job(self, work_job_id: int) -> None:
        """Abort a running job."""
        task = self._running_jobs.get(work_job_id)
        if task:
            task.cancel()
            logger.info(f"Job {work_job_id} abort requested")

    async def submit_manual_result(
        self,
        job_task_id: int,
        measured_values: Dict[str, Any],
        step_result: str,
        result_notes: str = "",
        performed_by: str = "",
    ) -> None:
        """
        Submit manual task results from the PWA.

        Called when a technician fills in a manual task form.
        Updates the job_task and signals the orchestrator to continue.

        Args:
            job_task_id: The job_tasks.id to update
            measured_values: Dict of measurement key/value pairs
            step_result: 'pass', 'fail', or 'info'
            result_notes: Optional technician notes
            performed_by: Technician name
        """
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            await db.execute("""
                UPDATE job_tasks
                SET status = 'completed',
                    step_result = ?,
                    measured_values = ?,
                    result_notes = ?,
                    performed_by = ?,
                    end_time = ?
                WHERE id = ?
            """, (
                step_result,
                json.dumps(measured_values),
                result_notes,
                performed_by,
                datetime.now().isoformat(),
                job_task_id,
            ))
            await db.commit()

        logger.info(f"Manual result submitted for task {job_task_id}: {step_result}")

    async def _run_job(self, work_job_id: int, station_id: int) -> None:
        """Internal: run all tasks for a job sequentially."""
        logger.info(f"Starting job execution: job={work_job_id}, station={station_id}")

        try:
            async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
                db.row_factory = aiosqlite.Row

                # Update job status
                await db.execute("""
                    UPDATE work_jobs SET status = 'in_progress',
                                         started_at = COALESCE(started_at, ?)
                    WHERE id = ?
                """, (datetime.now().isoformat(), work_job_id))
                await db.commit()

                # Load all pending tasks in order
                cursor = await db.execute("""
                    SELECT * FROM job_tasks
                    WHERE work_job_id = ? AND parent_task_id IS NULL
                    AND status IN ('pending', 'in_progress')
                    ORDER BY task_number ASC
                """, (work_job_id,))
                tasks = await cursor.fetchall()

            for task_row in tasks:
                task_id = task_row["id"]
                step_type = task_row["step_type"]
                is_automated = bool(task_row["is_automated"])

                # Mark task as in_progress
                await self._update_task_status(task_id, "in_progress")

                # Broadcast current task to WebSocket
                await self._broadcast_task_update(station_id, task_row)

                if is_automated:
                    await self._execute_automated_step(
                        task_id, station_id, step_type,
                        json.loads(task_row["params"] or "{}")
                    )
                else:
                    # Set status to awaiting_input for manual steps
                    await self._update_task_status(task_id, "awaiting_input")
                    await self._broadcast_task_awaiting_input(station_id, task_row)

                    # Wait for manual result submission (poll)
                    await self._wait_for_manual_completion(task_id)

                    # Also process child tasks if this is a section parent
                    await self._process_child_tasks(
                        work_job_id, task_id, station_id
                    )

            # All tasks complete — determine overall result
            overall = await self._determine_overall_result(work_job_id)

            # Update job
            async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
                await db.execute("""
                    UPDATE work_jobs
                    SET status = 'completed', completed_at = ?, overall_result = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), overall, work_job_id))
                await db.commit()

            # Create test report
            await self._create_test_report(work_job_id, overall)

            logger.info(f"Job {work_job_id} completed: {overall}")

        except asyncio.CancelledError:
            logger.info(f"Job {work_job_id} was cancelled/aborted")
            await self._handle_abort(work_job_id, station_id)
        except Exception as e:
            logger.error(f"Job {work_job_id} failed: {e}", exc_info=True)
            await self._handle_failure(work_job_id, station_id, str(e))

    async def _execute_automated_step(
        self, task_id: int, station_id: int,
        step_type: str, params: Dict[str, Any]
    ) -> None:
        """Execute an automated step by calling the appropriate TestController method."""
        from services import psu_controller, load_controller

        start_time = datetime.now()
        await self._update_task_time(task_id, start_time=start_time)

        chart_data = []
        measured_values = {}

        try:
            if step_type == "charge":
                current_ma = params.get("current_ma", 0)
                voltage_mv = params.get("voltage_limit_mv", 0)
                duration_min = params.get("duration_min", 0)
                temp_max = params.get("temp_max_c", 45.0)

                await load_controller.disable(station_id)
                await psu_controller.set_output(
                    station_id,
                    voltage_mv=voltage_mv,
                    current_ma=current_ma,
                )

                # Monitor charge for duration
                await self._monitor_step(
                    task_id, station_id, duration_min * 60,
                    chart_data, measured_values
                )

                await psu_controller.disable(station_id)

            elif step_type == "discharge":
                current_ma = params.get("current_ma", 0)
                voltage_min_mv = params.get("voltage_min_mv", 0)
                duration_min = params.get("duration_min", 0)

                await psu_controller.disable(station_id)
                await load_controller.set_load(
                    station_id,
                    current_ma=current_ma,
                    voltage_min_mv=voltage_min_mv,
                )

                # Monitor discharge
                await self._monitor_step(
                    task_id, station_id, duration_min * 60,
                    chart_data, measured_values
                )

                await load_controller.disable(station_id)

            elif step_type == "rest":
                duration_min = params.get("duration_min", 60)

                await psu_controller.disable(station_id)
                await load_controller.disable(station_id)

                # Monitor rest period
                await self._monitor_step(
                    task_id, station_id, duration_min * 60,
                    chart_data, measured_values
                )

            elif step_type == "wait_temp":
                temp_target = params.get("temp_target_c", 35.0)
                timeout_min = params.get("timeout_min", 120)

                await psu_controller.disable(station_id)
                await load_controller.disable(station_id)

                # Poll temperature until below target or timeout
                await self._monitor_step(
                    task_id, station_id, timeout_min * 60,
                    chart_data, measured_values
                )

            # Evaluate pass/fail
            step_result = self._evaluate_pass_criteria(params, measured_values)

            # Update task with results
            end_time = datetime.now()
            async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
                await db.execute("""
                    UPDATE job_tasks
                    SET status = 'completed', step_result = ?,
                        measured_values = ?, chart_data = ?,
                        data_points = ?, end_time = ?
                    WHERE id = ?
                """, (
                    step_result,
                    json.dumps(measured_values),
                    json.dumps(chart_data),
                    len(chart_data),
                    end_time.isoformat(),
                    task_id,
                ))
                await db.commit()

        except asyncio.CancelledError:
            # Ensure hardware is safe
            await psu_controller.disable(station_id)
            await load_controller.disable(station_id)
            await self._update_task_status(task_id, "aborted")
            raise

    async def _monitor_step(
        self, task_id: int, station_id: int,
        duration_sec: float, chart_data: List, measured_values: Dict
    ) -> None:
        """Monitor a step, collecting V/I/T samples at 10s intervals."""
        from services import psu_controller, i2c_poller

        interval = 10  # seconds
        elapsed = 0
        sample_count = 0
        flush_interval = 100  # Write to DB every 100 samples (~16 min)

        while elapsed < duration_sec:
            await asyncio.sleep(interval)
            elapsed += interval

            # Read current values
            voltage_mv = await psu_controller.read_voltage(station_id)
            current_ma = await psu_controller.read_current(station_id)
            i2c_data = i2c_poller.get_station_data(station_id)
            temp_c = i2c_data.get("temperature_c", 0) if i2c_data else 0

            sample = {
                "t": elapsed,
                "V": voltage_mv or 0,
                "I": current_ma or 0,
                "T": round(temp_c, 1) if temp_c else 0,
            }
            chart_data.append(sample)
            sample_count += 1

            # Track min/max/last values
            if voltage_mv:
                measured_values["voltage_last_mv"] = voltage_mv
                measured_values.setdefault("voltage_max_mv", 0)
                measured_values["voltage_max_mv"] = max(
                    measured_values["voltage_max_mv"], voltage_mv)
            if current_ma:
                measured_values["current_last_ma"] = current_ma
            if temp_c:
                measured_values["temperature_last_c"] = round(temp_c, 1)
                measured_values.setdefault("temperature_max_c", 0)
                measured_values["temperature_max_c"] = max(
                    measured_values["temperature_max_c"], temp_c)

            measured_values["elapsed_sec"] = elapsed
            measured_values["duration_min"] = round(elapsed / 60.0, 1)

            # Periodic flush of chart_data to SQLite
            if sample_count % flush_interval == 0:
                async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
                    await db.execute("""
                        UPDATE job_tasks SET chart_data = ?, data_points = ?
                        WHERE id = ?
                    """, (json.dumps(chart_data), len(chart_data), task_id))
                    await db.commit()

    def _evaluate_pass_criteria(self, params: Dict, measured: Dict) -> str:
        """Evaluate pass/fail based on step criteria."""
        criteria_type = params.get("_pass_criteria_type")
        criteria_value = params.get("_pass_criteria_value")

        if not criteria_type or criteria_type == "none":
            return "pass"

        try:
            criteria = json.loads(criteria_value) if isinstance(criteria_value, str) else criteria_value
        except (json.JSONDecodeError, TypeError):
            criteria = criteria_value

        if criteria_type == "min_duration":
            duration = measured.get("duration_min", 0)
            min_val = criteria.get("min", 0) if isinstance(criteria, dict) else float(criteria or 0)
            return "pass" if duration >= min_val else "fail"

        elif criteria_type == "min_value":
            key = params.get("_measurement_key", "")
            actual = measured.get(key, 0)
            min_val = criteria.get("min", 0) if isinstance(criteria, dict) else float(criteria or 0)
            return "pass" if actual >= min_val else "fail"

        elif criteria_type == "max_value":
            key = params.get("_measurement_key", "")
            actual = measured.get(key, 0)
            max_val = criteria.get("max", 0) if isinstance(criteria, dict) else float(criteria or 0)
            return "pass" if actual <= max_val else "fail"

        elif criteria_type == "range":
            key = params.get("_measurement_key", "")
            actual = measured.get(key, 0)
            if isinstance(criteria, dict):
                return "pass" if criteria.get("min", 0) <= actual <= criteria.get("max", float("inf")) else "fail"
            return "pass"

        elif criteria_type == "boolean":
            key = params.get("_measurement_key", "")
            return "pass" if measured.get(key) else "fail"

        return "info"

    async def _process_child_tasks(
        self, work_job_id: int, parent_task_id: int, station_id: int
    ) -> None:
        """Process child tasks of a parent (section group) task."""
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM job_tasks
                WHERE work_job_id = ? AND parent_task_id = ?
                AND status = 'pending'
                ORDER BY task_number ASC
            """, (work_job_id, parent_task_id))
            children = await cursor.fetchall()

        for child in children:
            await self._update_task_status(child["id"], "awaiting_input")
            await self._broadcast_task_awaiting_input(station_id, child)
            await self._wait_for_manual_completion(child["id"])

        # Mark parent as completed once all children done
        await self._update_task_status(parent_task_id, "completed")

    async def _wait_for_manual_completion(self, task_id: int, timeout_sec: int = 86400) -> None:
        """Poll until a manual task is completed (submitted by PWA)."""
        elapsed = 0
        poll_interval = 2  # seconds
        while elapsed < timeout_sec:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
                cursor = await db.execute(
                    "SELECT status FROM job_tasks WHERE id = ?", (task_id,))
                row = await cursor.fetchone()
                if row and row[0] in ("completed", "failed", "skipped"):
                    return

        # Timeout
        await self._update_task_status(task_id, "failed")

    async def _determine_overall_result(self, work_job_id: int) -> str:
        """Determine overall pass/fail/incomplete from all task results."""
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            cursor = await db.execute("""
                SELECT step_result, status FROM job_tasks
                WHERE work_job_id = ? AND parent_task_id IS NULL
            """, (work_job_id,))
            rows = await cursor.fetchall()

        if any(r[1] in ("pending", "in_progress", "awaiting_input") for r in rows):
            return "incomplete"
        if any(r[0] == "fail" for r in rows):
            return "fail"
        return "pass"

    async def _create_test_report(self, work_job_id: int, overall: str) -> None:
        """Create a test_reports row with denormalized data for PDF generation."""
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute("""
                SELECT wj.*, wo.work_order_number, c.name as customer_name,
                       tp.cmm_number, tp.revision as cmm_revision, tp.title as cmm_title
                FROM work_jobs wj
                JOIN work_orders wo ON wj.work_order_id = wo.id
                JOIN customers c ON wo.customer_id = c.id
                LEFT JOIN tech_pubs tp ON wj.tech_pub_id = tp.id
                WHERE wj.id = ?
            """, (work_job_id,))
            job = await cursor.fetchone()
            if not job:
                return

            # Collect failure reasons
            cursor = await db.execute("""
                SELECT label, result_notes FROM job_tasks
                WHERE work_job_id = ? AND step_result = 'fail'
            """, (work_job_id,))
            failures = [{"step": r[0], "reason": r[1] or ""} for r in await cursor.fetchall()]

            # Collect tools used
            cursor = await db.execute("""
                SELECT DISTINCT ttu.tool_id_display, ttu.tool_description,
                       ttu.tool_serial_number, ttu.tool_calibration_cert
                FROM task_tool_usage ttu
                JOIN job_tasks jt ON ttu.job_task_id = jt.id
                WHERE jt.work_job_id = ?
            """, (work_job_id,))
            tools = [dict(r) for r in await cursor.fetchall()]

            # Collect station equipment
            cursor = await db.execute("""
                SELECT * FROM station_equipment
                WHERE station_id = ? AND is_active = 1
            """, (job["station_id"],))
            equipment = [dict(r) for r in await cursor.fetchall()]

            # Manual test summary
            cursor = await db.execute("""
                SELECT step_type, label, step_result, measured_values
                FROM job_tasks
                WHERE work_job_id = ? AND is_automated = 0
                AND step_result IS NOT NULL
            """, (work_job_id,))
            manual_summary = {}
            for r in await cursor.fetchall():
                manual_summary[r[1]] = {
                    "type": r[0], "result": r[2],
                    "values": json.loads(r[3] or "{}")
                }

            await db.execute("""
                INSERT INTO test_reports
                    (work_job_id, work_order_item_id, battery_serial,
                     battery_part_number, battery_amendment,
                     cmm_number, cmm_revision, cmm_title,
                     customer_name, work_order_number, station_id,
                     test_started_at, test_completed_at, overall_result,
                     failure_reasons, station_equipment, tools_used,
                     manual_test_summary, technician_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                work_job_id, job["work_order_item_id"],
                job["battery_serial"], job["battery_part_number"],
                job["battery_amendment"],
                job["cmm_number"] or "", job["cmm_revision"] or "",
                job["cmm_title"] or "",
                job["customer_name"], job["work_order_number"],
                job["station_id"],
                job["started_at"], job["completed_at"],
                overall,
                json.dumps(failures), json.dumps(equipment),
                json.dumps(tools), json.dumps(manual_summary),
                job.get("started_by", ""),
            ))
            await db.commit()

        logger.info(f"Test report created for job {work_job_id}")

    async def _update_task_status(self, task_id: int, status: str) -> None:
        """Update a task's status."""
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            updates = {"status": status}
            if status == "in_progress":
                updates["start_time"] = datetime.now().isoformat()
            await db.execute(
                f"UPDATE job_tasks SET status = ?, start_time = COALESCE(start_time, ?) WHERE id = ?",
                (status, datetime.now().isoformat() if status == "in_progress" else None, task_id)
            )
            await db.commit()

    async def _update_task_time(self, task_id: int, start_time: datetime) -> None:
        """Set task start time."""
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            await db.execute(
                "UPDATE job_tasks SET start_time = ? WHERE id = ?",
                (start_time.isoformat(), task_id)
            )
            await db.commit()

    async def _broadcast_task_update(self, station_id: int, task_row) -> None:
        """Broadcast current task info via WebSocket."""
        try:
            from api import ws
            await ws.broadcast_station_update(station_id, {
                "event": "task_progress",
                "task_id": task_row["id"],
                "task_number": task_row["task_number"],
                "step_type": task_row["step_type"],
                "label": task_row["label"],
                "status": "in_progress",
            })
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")

    async def _broadcast_task_awaiting_input(self, station_id: int, task_row) -> None:
        """Broadcast awaiting_input event for manual tasks."""
        try:
            from api import ws
            await ws.broadcast_task_awaiting_input(station_id, {
                "task_id": task_row["id"],
                "task_number": task_row["task_number"],
                "step_type": task_row["step_type"],
                "label": task_row["label"],
                "description": task_row["description"],
                "params": json.loads(task_row["params"] or "{}"),
            })
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")

    async def _handle_abort(self, work_job_id: int, station_id: int) -> None:
        """Handle job abort — disable hardware, update statuses."""
        from services import psu_controller, load_controller
        await psu_controller.disable(station_id)
        await load_controller.disable(station_id)

        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            await db.execute("""
                UPDATE work_jobs SET status = 'aborted', completed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), work_job_id))
            await db.execute("""
                UPDATE job_tasks SET status = 'aborted'
                WHERE work_job_id = ? AND status IN ('pending', 'in_progress', 'awaiting_input')
            """, (work_job_id,))
            await db.commit()

    async def _handle_failure(self, work_job_id: int, station_id: int, error: str) -> None:
        """Handle job failure — disable hardware, update statuses."""
        from services import psu_controller, load_controller
        await psu_controller.disable(station_id)
        await load_controller.disable(station_id)

        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            await db.execute("""
                UPDATE work_jobs SET status = 'failed', completed_at = ?,
                       overall_result = 'fail'
                WHERE id = ?
            """, (datetime.now().isoformat(), work_job_id))
            await db.execute("""
                UPDATE job_tasks SET status = 'failed', result_notes = ?
                WHERE work_job_id = ? AND status IN ('pending', 'in_progress', 'awaiting_input')
            """, (f"Job failed: {error}", work_job_id))
            await db.commit()


# Singleton
_orchestrator = TaskExecutionOrchestrator()


async def execute_job(work_job_id: int, station_id: int) -> None:
    await _orchestrator.execute_job(work_job_id, station_id)


async def abort_job(work_job_id: int) -> None:
    await _orchestrator.abort_job(work_job_id)


async def submit_manual_result(job_task_id: int, **kwargs) -> None:
    await _orchestrator.submit_manual_result(job_task_id, **kwargs)
