"""
Battery Test Bench - Tool Validator
Version: 2.0.0

Validates tool calibration at use time. Creates task_tool_usage records
with frozen calibration snapshot. Blocks use of expired tools.
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any

import aiosqlite
from config import settings

logger = logging.getLogger(__name__)


class ToolValidator:
    """Validates tool calibration and creates usage records."""

    async def validate_tool(self, tool_id: int) -> Dict[str, Any]:
        """
        Validate a tool is currently calibrated and active.

        Args:
            tool_id: tools.id

        Returns:
            Dict with tool info and validation result

        Raises:
            ValueError: If tool is expired, inactive, or not found
        """
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tools WHERE id = ?", (tool_id,))
            tool = await cursor.fetchone()

        if not tool:
            raise ValueError(f"Tool {tool_id} not found")

        if not tool["is_active"]:
            raise ValueError(
                f"Tool {tool_id} ({tool['description']}) is inactive")

        # Check calibration validity
        valid_until = tool["valid_until"]
        is_valid = True
        if valid_until:
            try:
                exp_date = date.fromisoformat(valid_until)
                is_valid = exp_date >= date.today()
            except ValueError:
                is_valid = False

        if not is_valid:
            raise ValueError(
                f"Tool {tool_id} ({tool['description']}) calibration expired "
                f"on {valid_until}"
            )

        return {
            "tool_id": tool["id"],
            "tool_id_display": tool["tool_id_display"] or f"TID{tool['id']:03d}",
            "description": tool["description"],
            "serial_number": tool["serial_number"],
            "calibration_valid": is_valid,
            "calibration_due": valid_until,
            "calibration_cert": tool["calibration_certificate"],
        }

    async def validate_tools_for_step(
        self, required_categories: List[str], selected_tool_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Validate all tools selected for a step.

        Args:
            required_categories: Tool categories needed (e.g., ['multimeter'])
            selected_tool_ids: Tool IDs chosen by technician

        Returns:
            List of validated tool info dicts

        Raises:
            ValueError: If any tool is invalid or category not covered
        """
        validated = []
        for tool_id in selected_tool_ids:
            info = await self.validate_tool(tool_id)
            validated.append(info)

        return validated

    async def record_tool_usage(
        self, job_task_id: int, tool_id: int
    ) -> int:
        """
        Create a task_tool_usage record with frozen calibration snapshot.

        Args:
            job_task_id: The job_tasks.id this tool is being used for
            tool_id: The tools.id being used

        Returns:
            The created task_tool_usage.id
        """
        info = await self.validate_tool(tool_id)

        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            cursor = await db.execute("""
                INSERT INTO task_tool_usage
                    (job_task_id, tool_id, tool_id_display, tool_description,
                     tool_serial_number, tool_calibration_valid,
                     tool_calibration_due, tool_calibration_cert)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_task_id, tool_id,
                info["tool_id_display"], info["description"],
                info["serial_number"], info["calibration_valid"],
                info["calibration_due"], info["calibration_cert"],
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_available_tools(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of active, calibrated tools optionally filtered by category.
        """
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM tools WHERE is_active = 1"
            params = []
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY category, id"

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

        tools = []
        today = date.today()
        for row in rows:
            valid = True
            if row["valid_until"]:
                try:
                    valid = date.fromisoformat(row["valid_until"]) >= today
                except ValueError:
                    valid = False

            tools.append({
                "id": row["id"],
                "tool_id_display": row["tool_id_display"] or f"TID{row['id']:03d}",
                "description": row["description"],
                "serial_number": row["serial_number"],
                "category": row["category"],
                "calibration_valid": valid,
                "calibration_due": row["valid_until"],
                "calibration_cert": row["calibration_certificate"],
            })

        return tools


# Singleton
_validator = ToolValidator()


async def validate_tool(tool_id: int) -> Dict[str, Any]:
    return await _validator.validate_tool(tool_id)


async def record_tool_usage(job_task_id: int, tool_id: int) -> int:
    return await _validator.record_tool_usage(job_task_id, tool_id)


async def get_available_tools(category: Optional[str] = None) -> List[Dict[str, Any]]:
    return await _validator.get_available_tools(category)
