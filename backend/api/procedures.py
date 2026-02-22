"""
Battery Test Bench - Procedures API (Tech Pub Sections & Steps)
Version: 2.0.0

CRUD for tech_pub_sections and procedure_steps.
Procedure resolution endpoint for work order items.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import aiosqlite
import logging

from config import settings
from services.procedure_resolver import ProcedureResolver

router = APIRouter(prefix="/procedures", tags=["procedures"])
logger = logging.getLogger(__name__)


class SectionCreate(BaseModel):
    tech_pub_id: int
    section_number: str
    title: str
    section_type: str
    description: Optional[str] = None
    sort_order: int = 0
    is_mandatory: bool = True
    condition_type: str = "always"
    condition_key: Optional[str] = None
    condition_value: Optional[str] = None


class StepCreate(BaseModel):
    section_id: int
    step_number: int
    step_type: str
    label: str
    description: Optional[str] = None
    param_source: str = "fixed"
    param_overrides: Optional[dict] = None
    pass_criteria_type: Optional[str] = None
    pass_criteria_value: Optional[str] = None
    measurement_key: Optional[str] = None
    measurement_unit: Optional[str] = None
    measurement_label: Optional[str] = None
    estimated_duration_min: float = 0
    is_automated: bool = False
    requires_tools: Optional[List[str]] = None
    sort_order: int = 0


@router.get("/sections/{tech_pub_id}")
async def get_sections(tech_pub_id: int):
    """Get all sections for a tech pub, ordered by sort_order."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM tech_pub_sections
            WHERE tech_pub_id = ? AND is_active = 1
            ORDER BY sort_order ASC
        """, (tech_pub_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/sections")
async def create_section(data: SectionCreate):
    """Create a new tech pub section."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO tech_pub_sections
                (tech_pub_id, section_number, title, section_type,
                 description, sort_order, is_mandatory,
                 condition_type, condition_key, condition_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.tech_pub_id, data.section_number, data.title,
            data.section_type, data.description, data.sort_order,
            data.is_mandatory, data.condition_type,
            data.condition_key, data.condition_value,
        ))
        await db.commit()
        return {"id": cursor.lastrowid, "message": "Section created"}


@router.get("/steps/{section_id}")
async def get_steps(section_id: int):
    """Get all steps for a section, ordered by sort_order."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM procedure_steps
            WHERE section_id = ? AND is_active = 1
            ORDER BY sort_order ASC
        """, (section_id,))
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["param_overrides"] = json.loads(d.get("param_overrides") or "{}")
            d["requires_tools"] = json.loads(d.get("requires_tools") or "[]")
            results.append(d)
        return results


@router.post("/steps")
async def create_step(data: StepCreate):
    """Create a new procedure step."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO procedure_steps
                (section_id, step_number, step_type, label, description,
                 param_source, param_overrides, pass_criteria_type,
                 pass_criteria_value, measurement_key, measurement_unit,
                 measurement_label, estimated_duration_min, is_automated,
                 requires_tools, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.section_id, data.step_number, data.step_type,
            data.label, data.description, data.param_source,
            json.dumps(data.param_overrides or {}),
            data.pass_criteria_type, data.pass_criteria_value,
            data.measurement_key, data.measurement_unit,
            data.measurement_label, data.estimated_duration_min,
            data.is_automated,
            json.dumps(data.requires_tools or []),
            data.sort_order,
        ))
        await db.commit()
        return {"id": cursor.lastrowid, "message": "Step created"}


@router.get("/resolve/{work_order_item_id}")
async def resolve_procedure(
    work_order_item_id: int,
    service_type: str = "capacity_test",
    months_since_service: int = 0,
):
    """
    Resolve the complete procedure for a work order item.
    Returns all applicable sections and steps based on battery model,
    feature flags, amendment, age, and service type.
    """
    try:
        resolver = ProcedureResolver()
        procedure = await resolver.resolve_procedure(
            work_order_item_id, service_type, months_since_service)

        return {
            "tech_pub_id": procedure.tech_pub_id,
            "cmm_number": procedure.cmm_number,
            "cmm_revision": procedure.cmm_revision,
            "cmm_title": procedure.cmm_title,
            "part_number": procedure.part_number,
            "amendment": procedure.amendment,
            "service_type": procedure.service_type,
            "total_steps": procedure.total_steps,
            "estimated_hours": round(procedure.estimated_total_hours, 1),
            "sections": [
                {
                    "section_id": s.section_id,
                    "section_number": s.section_number,
                    "title": s.title,
                    "section_type": s.section_type,
                    "is_mandatory": s.is_mandatory,
                    "steps": [
                        {
                            "step_id": st.step_id,
                            "step_number": st.step_number,
                            "step_type": st.step_type,
                            "label": st.label,
                            "is_automated": st.is_automated,
                            "estimated_duration_min": st.estimated_duration_min,
                            "requires_tools": st.requires_tools,
                        }
                        for st in s.steps
                    ]
                }
                for s in procedure.sections
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Procedure resolution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
