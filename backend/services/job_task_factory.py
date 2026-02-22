"""
Battery Test Bench - Job Task Factory
Version: 2.0.0

Creates job_tasks rows from a ResolvedProcedure. Resolves parameters from
EEPROM/profile/fixed sources. Creates parent-child hierarchies for multi-step
sections (e.g., a section parent with individual step children).
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import aiosqlite
from config import settings
from services.procedure_resolver import ResolvedProcedure, ResolvedSection, ResolvedStep

logger = logging.getLogger(__name__)


class JobTaskFactory:
    """Creates job_tasks rows from a resolved procedure."""

    async def create_tasks_for_job(
        self,
        work_job_id: int,
        procedure: ResolvedProcedure,
        eeprom_params: Optional[Dict[str, Any]] = None,
    ) -> List[int]:
        """
        Create all job_tasks for a work job from a resolved procedure.

        Creates a flat task list ordered by section sort_order then step sort_order.
        Each step becomes one job_task row. Section-level parent tasks are created
        for manual_test sections that have multiple steps (for grouping in UI).

        Args:
            work_job_id: The work_jobs.id to create tasks for
            procedure: ResolvedProcedure from ProcedureResolver
            eeprom_params: Optional EEPROM-sourced test parameters dict

        Returns:
            List of created job_task IDs
        """
        task_ids = []
        task_number = 0

        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            for section in procedure.sections:
                parent_task_id = None

                # Create a parent task for manual_test sections with multiple steps
                if section.section_type in ("manual_test", "inspection") and len(section.steps) > 1:
                    task_number += 1
                    parent_task_id = await self._insert_task(
                        db,
                        work_job_id=work_job_id,
                        parent_task_id=None,
                        section_id=section.section_id,
                        step_id=None,
                        task_number=task_number,
                        step_type="operator_action",
                        label=f"{section.section_number} {section.title}",
                        description=section.description,
                        is_automated=False,
                        source="procedure",
                        params="{}",
                    )
                    task_ids.append(parent_task_id)

                for step in section.steps:
                    task_number += 1
                    params = self._resolve_params(step, eeprom_params or {},
                                                  procedure.context)

                    task_id = await self._insert_task(
                        db,
                        work_job_id=work_job_id,
                        parent_task_id=parent_task_id,
                        section_id=section.section_id,
                        step_id=step.step_id,
                        task_number=task_number,
                        step_type=step.step_type,
                        label=step.label,
                        description=step.description,
                        is_automated=step.is_automated,
                        source="procedure",
                        params=json.dumps(params),
                    )
                    task_ids.append(task_id)

            await db.commit()

        logger.info(f"Created {len(task_ids)} job_tasks for work_job {work_job_id}")
        return task_ids

    def _resolve_params(self, step: ResolvedStep,
                        eeprom_params: Dict[str, Any],
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve step parameters from the appropriate source.

        param_source:
        - 'fixed': Use param_overrides as-is
        - 'eeprom': Map step_type to EEPROM fields, overlay with param_overrides
        - 'profile': Map to battery_profiles fields
        - 'previous_step': Marker for orchestrator to resolve at runtime
        """
        params = {}

        if step.param_source == "fixed":
            params = dict(step.param_overrides)

        elif step.param_source == "eeprom":
            # Map step type to relevant EEPROM parameters
            if step.step_type == "charge":
                params = {
                    "current_ma": eeprom_params.get("standard_charge_current_ma", 0),
                    "voltage_limit_mv": eeprom_params.get("charge_voltage_limit_mv", 0),
                    "duration_min": eeprom_params.get("standard_charge_duration_min", 0),
                    "temp_max_c": eeprom_params.get("max_charge_temp_c", 45.0),
                }
            elif step.step_type == "discharge":
                params = {
                    "current_ma": eeprom_params.get("cap_test_discharge_current_ma", 0),
                    "voltage_min_mv": eeprom_params.get("cap_test_end_voltage_mv", 0),
                    "duration_min": eeprom_params.get("cap_test_max_duration_min", 0),
                    "temp_max_c": eeprom_params.get("max_discharge_temp_c", 55.0),
                }
            elif step.step_type == "rest":
                params = {
                    "duration_min": eeprom_params.get("cap_test_rest_before_min", 60),
                }
            elif step.step_type == "wait_temp":
                params = {
                    "temp_target_c": eeprom_params.get("max_charge_temp_c", 35.0),
                    "timeout_min": 120,
                }
            # Overlay with any explicit overrides from procedure_steps
            params.update(step.param_overrides)

        elif step.param_source == "profile":
            params = dict(step.param_overrides)

        elif step.param_source == "previous_step":
            params = {"_resolve_at_runtime": True}
            params.update(step.param_overrides)

        # Add pass criteria if defined
        if step.pass_criteria_type and step.pass_criteria_type != "none":
            params["_pass_criteria_type"] = step.pass_criteria_type
            params["_pass_criteria_value"] = step.pass_criteria_value

        # Add measurement metadata
        if step.measurement_key:
            params["_measurement_key"] = step.measurement_key
            params["_measurement_unit"] = step.measurement_unit
            params["_measurement_label"] = step.measurement_label

        return params

    async def _insert_task(
        self,
        db,
        work_job_id: int,
        parent_task_id: Optional[int],
        section_id: Optional[int],
        step_id: Optional[int],
        task_number: int,
        step_type: str,
        label: str,
        description: Optional[str],
        is_automated: bool,
        source: str,
        params: str,
    ) -> int:
        """Insert a single job_task row and return its ID."""
        cursor = await db.execute("""
            INSERT INTO job_tasks
                (work_job_id, parent_task_id, section_id, step_id,
                 task_number, step_type, label, description,
                 is_automated, source, status, params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            work_job_id, parent_task_id, section_id, step_id,
            task_number, step_type, label, description,
            is_automated, source, params,
        ))
        return cursor.lastrowid
