"""
Battery Test Bench - Procedure Resolver
Version: 2.0.0

Evaluates which tech_pub_sections and procedure_steps apply to a specific
battery based on feature_flags, amendment, age, and service type.
Replaces all hardcoded logic in test_rule_engine.py.

Key method: resolve_procedure(work_order_item_id, service_type) → ResolvedProcedure
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import aiosqlite
from config import settings
from services.condition_evaluator import ConditionEvaluator

logger = logging.getLogger(__name__)


@dataclass
class ResolvedStep:
    """A single resolved procedure step with parameters ready for execution."""
    step_id: int
    section_id: int
    step_number: int
    step_type: str
    label: str
    description: Optional[str]
    param_source: str
    param_overrides: Dict[str, Any]
    pass_criteria_type: Optional[str]
    pass_criteria_value: Optional[str]
    measurement_key: Optional[str]
    measurement_unit: Optional[str]
    measurement_label: Optional[str]
    estimated_duration_min: float
    is_automated: bool
    requires_tools: List[str]
    sort_order: int


@dataclass
class ResolvedSection:
    """A resolved CMM section with its applicable steps."""
    section_id: int
    section_number: str
    title: str
    section_type: str
    description: Optional[str]
    sort_order: int
    is_mandatory: bool
    steps: List[ResolvedStep] = field(default_factory=list)


@dataclass
class ResolvedProcedure:
    """Complete resolved procedure for a battery — sections and steps filtered
    by conditions, ordered, and ready for job_task creation."""
    tech_pub_id: int
    cmm_number: str
    cmm_revision: str
    cmm_title: str
    part_number: str
    amendment: str
    profile_id: Optional[int]
    service_type: str
    sections: List[ResolvedSection] = field(default_factory=list)
    estimated_total_hours: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_steps(self) -> int:
        return sum(len(s.steps) for s in self.sections)


class ProcedureResolver:
    """Resolves which CMM sections/steps apply to a specific battery."""

    def __init__(self):
        self.evaluator = ConditionEvaluator()

    async def resolve_procedure(
        self,
        work_order_item_id: int,
        service_type: str,
        months_since_service: int = 0,
    ) -> ResolvedProcedure:
        """
        Resolve the complete procedure for a work order item.

        1. Look up the battery's part_number/amendment from work_order_items
        2. Find the matching tech_pub via tech_pub_applicability
        3. Load battery_profiles.feature_flags for the part/amendment
        4. Evaluate each tech_pub_section's condition against context
        5. For passing sections, evaluate each procedure_step's condition
        6. Return ordered ResolvedProcedure ready for job_task creation

        Args:
            work_order_item_id: The work order item to resolve for
            service_type: Service type string (capacity_test, reconditioning, etc.)
            months_since_service: Months since last service (for age rules)

        Returns:
            ResolvedProcedure with applicable sections and steps
        """
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 1. Get work order item details
            cursor = await db.execute("""
                SELECT woi.*, wo.service_type as wo_service_type
                FROM work_order_items woi
                JOIN work_orders wo ON woi.work_order_id = wo.id
                WHERE woi.id = ?
            """, (work_order_item_id,))
            item = await cursor.fetchone()
            if not item:
                raise ValueError(f"Work order item {work_order_item_id} not found")

            part_number = item["part_number"]
            amendment = item["amendment"] or ""

            # 2. Find matching tech pub
            cursor = await db.execute("""
                SELECT tp.* FROM tech_pubs tp
                JOIN tech_pub_applicability tpa ON tpa.tech_pub_id = tp.id
                WHERE tpa.part_number = ? AND tp.is_active = 1
                ORDER BY tp.id DESC LIMIT 1
            """, (part_number,))
            tech_pub = await cursor.fetchone()

            if not tech_pub:
                # Fallback: try the old JSON column
                cursor = await db.execute("""
                    SELECT * FROM tech_pubs
                    WHERE applicable_part_numbers LIKE ? AND is_active = 1
                    ORDER BY id DESC LIMIT 1
                """, (f'%{part_number}%',))
                tech_pub = await cursor.fetchone()

            if not tech_pub:
                raise ValueError(f"No tech pub found for part number {part_number}")

            # 3. Load battery profile + feature flags
            cursor = await db.execute("""
                SELECT * FROM battery_profiles
                WHERE part_number = ?
                AND (amendment = ? OR (amendment IS NULL AND ? = ''))
                AND is_active = 1
                ORDER BY id DESC LIMIT 1
            """, (part_number, amendment, amendment))
            profile = await cursor.fetchone()

            feature_flags = {}
            profile_id = None
            if profile:
                profile_id = profile["id"]
                ff = profile["feature_flags"] if "feature_flags" in profile.keys() else "{}"
                feature_flags = json.loads(ff) if ff else {}

            # 4. Build evaluation context
            age_months = item["age_months"] or 0
            context = {
                "feature_flags": feature_flags,
                "amendment": amendment,
                "age_months": age_months,
                "months_since_service": months_since_service,
                "service_type": service_type,
                "part_number": part_number,
            }

            # 5. Load and filter sections
            cursor = await db.execute("""
                SELECT * FROM tech_pub_sections
                WHERE tech_pub_id = ? AND is_active = 1
                ORDER BY sort_order ASC
            """, (tech_pub["id"],))
            sections_rows = await cursor.fetchall()

            resolved_sections = []
            total_duration = 0.0

            for sec_row in sections_rows:
                # Evaluate section condition
                if not self.evaluator.evaluate(
                    sec_row["condition_type"],
                    sec_row["condition_key"],
                    sec_row["condition_value"],
                    context
                ):
                    continue

                # 6. Load and filter steps for this section
                cursor = await db.execute("""
                    SELECT * FROM procedure_steps
                    WHERE section_id = ? AND is_active = 1
                    ORDER BY sort_order ASC
                """, (sec_row["id"],))
                step_rows = await cursor.fetchall()

                resolved_steps = []
                for step_row in step_rows:
                    # Evaluate step condition
                    if not self.evaluator.evaluate(
                        step_row["condition_type"],
                        step_row["condition_key"],
                        step_row["condition_value"],
                        context
                    ):
                        continue

                    overrides = json.loads(step_row["param_overrides"] or "{}")
                    tools = json.loads(step_row["requires_tools"] or "[]")

                    resolved_steps.append(ResolvedStep(
                        step_id=step_row["id"],
                        section_id=sec_row["id"],
                        step_number=step_row["step_number"],
                        step_type=step_row["step_type"],
                        label=step_row["label"],
                        description=step_row["description"],
                        param_source=step_row["param_source"],
                        param_overrides=overrides,
                        pass_criteria_type=step_row["pass_criteria_type"],
                        pass_criteria_value=step_row["pass_criteria_value"],
                        measurement_key=step_row["measurement_key"],
                        measurement_unit=step_row["measurement_unit"],
                        measurement_label=step_row["measurement_label"],
                        estimated_duration_min=step_row["estimated_duration_min"] or 0,
                        is_automated=bool(step_row["is_automated"]),
                        requires_tools=tools,
                        sort_order=step_row["sort_order"],
                    ))
                    total_duration += step_row["estimated_duration_min"] or 0

                section = ResolvedSection(
                    section_id=sec_row["id"],
                    section_number=sec_row["section_number"],
                    title=sec_row["title"],
                    section_type=sec_row["section_type"],
                    description=sec_row["description"],
                    sort_order=sec_row["sort_order"],
                    is_mandatory=bool(sec_row["is_mandatory"]),
                    steps=resolved_steps,
                )
                resolved_sections.append(section)

            procedure = ResolvedProcedure(
                tech_pub_id=tech_pub["id"],
                cmm_number=tech_pub["cmm_number"],
                cmm_revision=tech_pub["revision"] or "",
                cmm_title=tech_pub["title"],
                part_number=part_number,
                amendment=amendment,
                profile_id=profile_id,
                service_type=service_type,
                sections=resolved_sections,
                estimated_total_hours=total_duration / 60.0,
                context=context,
            )

            logger.info(
                f"Resolved procedure: {tech_pub['cmm_number']} for {part_number} "
                f"/ {service_type} — {len(resolved_sections)} sections, "
                f"{procedure.total_steps} steps, "
                f"~{procedure.estimated_total_hours:.1f}h"
            )

            return procedure
