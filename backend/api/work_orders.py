"""
Battery Test Bench - Work Order API Endpoints (Orion Technik)
Version: 1.3.0

Changelog:
v1.3.0 (2026-02-22): Simplified intake (single battery), open/closed filter,
                      items key, DELETE endpoint, full PUT model
v1.2.4 (2026-02-16): Orion Technik WO is primary reference (auto-generated);
                      customer reference is optional; added battery revision field
v1.2.3 (2026-02-16): Simplified to battery intake model
v1.2.1 (2026-02-16): Initial work order CRUD for service shop model
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import aiosqlite
import logging

from config import settings

router = APIRouter(prefix="/work-orders", tags=["work-orders"])
logger = logging.getLogger(__name__)


# -- Pydantic Models --

class BatteryIntakeItem(BaseModel):
    """Single battery being received for testing"""
    serial_number: str
    part_number: str
    revision: str
    amendment: Optional[str] = None
    reported_condition: Optional[str] = None


class WorkOrderIntake(BaseModel):
    """
    Battery intake form — accepts both single-battery simplified flow
    and legacy multi-battery flow.
    """
    work_order_number: Optional[str] = None
    customer_id: int
    customer_reference: Optional[str] = Field(None, description="Customer's own reference (optional)")
    service_type: str = "inspection_test"
    customer_notes: Optional[str] = None
    internal_work_number: Optional[str] = None
    # Single battery (new simplified flow)
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    revision: Optional[str] = ""
    amendment: Optional[str] = None
    # Legacy multi-battery
    batteries: Optional[List[BatteryIntakeItem]] = None


class WorkOrderUpdate(BaseModel):
    work_order_number: Optional[str] = None
    customer_id: Optional[int] = None
    service_type: Optional[str] = None
    internal_work_number: Optional[str] = None
    status: Optional[str] = None
    technician_notes: Optional[str] = None
    assigned_technician: Optional[str] = None


# -- Helper: Generate internal tracking number --

async def _generate_tracking_number(db) -> str:
    year = datetime.now().year
    prefix = settings.WORK_ORDER_PREFIX
    cursor = await db.execute(
        "SELECT COUNT(*) FROM work_orders WHERE work_order_number LIKE ?",
        (f"{prefix}-{year}-%",)
    )
    row = await cursor.fetchone()
    seq = (row[0] or 0) + 1
    return f"{prefix}-{year}-{seq:05d}"


# -- Endpoints --

@router.get("/")
async def list_work_orders(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 100
):
    """List work orders with optional filtering"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT wo.*, c.name as customer_name,
                   COUNT(woi.id) as battery_count
            FROM work_orders wo
            LEFT JOIN customers c ON wo.customer_id = c.id
            LEFT JOIN work_order_items woi ON woi.work_order_id = wo.id
        """
        params = []
        conditions = []

        if status:
            if status == "open":
                conditions.append("wo.status IN ('received', 'in_progress')")
            elif status == "closed":
                conditions.append("wo.status IN ('completed', 'closed')")
            else:
                conditions.append("wo.status = ?")
                params.append(status)
        if customer_id:
            conditions.append("wo.customer_id = ?")
            params.append(customer_id)
        if search:
            conditions.append(
                "(wo.customer_reference LIKE ? OR wo.work_order_number LIKE ?)"
            )
            params.extend([f"%{search}%", f"%{search}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY wo.id ORDER BY wo.received_date DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{wo_id}")
async def get_work_order(wo_id: int):
    """Get work order details including battery items"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT wo.*, c.name as customer_name, c.email as customer_email
            FROM work_orders wo
            LEFT JOIN customers c ON wo.customer_id = c.id
            WHERE wo.id = ?
        """, (wo_id,))
        wo = await cursor.fetchone()
        if not wo:
            raise HTTPException(status_code=404, detail="Work order not found")

        cursor = await db.execute("""
            SELECT woi.*, bp.description as profile_description
            FROM work_order_items woi
            LEFT JOIN battery_profiles bp ON woi.profile_id = bp.id
            WHERE woi.work_order_id = ?
        """, (wo_id,))
        items = await cursor.fetchall()

        result = dict(wo)
        result['items'] = [dict(item) for item in items]
        return result


@router.post("/")
async def receive_batteries(data: WorkOrderIntake):
    """
    Record battery intake — accepts single-battery or multi-battery.
    WO number is user-provided or auto-generated.
    """
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Use provided WO number or auto-generate
        wo_number = data.work_order_number
        if not wo_number:
            wo_number = await _generate_tracking_number(db)

        cursor = await db.execute("""
            INSERT INTO work_orders
                (work_order_number, customer_reference, customer_id,
                 service_type, received_date, customer_notes,
                 internal_work_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_number, data.customer_reference, data.customer_id,
            data.service_type, datetime.now().isoformat(),
            data.customer_notes, data.internal_work_number
        ))
        wo_id = cursor.lastrowid

        # Build battery list: use batteries if provided, else single battery fields
        batteries: List[BatteryIntakeItem] = []
        if data.batteries:
            batteries = data.batteries
        elif data.part_number and data.serial_number:
            batteries = [BatteryIntakeItem(
                serial_number=data.serial_number,
                part_number=data.part_number,
                revision=data.revision or "",
                amendment=data.amendment,
            )]

        # Add battery items
        for battery in batteries:
            # Auto-match battery profile by part number
            profile_cursor = await db.execute("""
                SELECT id FROM battery_profiles
                WHERE part_number = ? AND (amendment = ? OR ? IS NULL)
                AND is_active = 1 LIMIT 1
            """, (battery.part_number, battery.amendment, battery.amendment))
            profile_row = await profile_cursor.fetchone()
            profile_id = profile_row[0] if profile_row else None

            await db.execute("""
                INSERT INTO work_order_items
                    (work_order_id, serial_number, part_number, revision,
                     amendment, profile_id, reported_condition)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                wo_id, battery.serial_number, battery.part_number,
                battery.revision, battery.amendment, profile_id,
                battery.reported_condition
            ))

        await db.commit()

        # Fetch the created work order to return full object
        db.row_factory = aiosqlite.Row
        wo_cursor = await db.execute("""
            SELECT wo.*, c.name as customer_name,
                   COUNT(woi.id) as item_count
            FROM work_orders wo
            LEFT JOIN customers c ON wo.customer_id = c.id
            LEFT JOIN work_order_items woi ON woi.work_order_id = wo.id
            WHERE wo.id = ?
            GROUP BY wo.id
        """, (wo_id,))
        wo_row = await wo_cursor.fetchone()

        return {
            "status": "ok",
            "message": f"WO {wo_number} created with {len(batteries)} batteries",
            "work_order": dict(wo_row) if wo_row else {"id": wo_id, "work_order_number": wo_number}
        }


@router.put("/{wo_id}")
async def update_work_order(wo_id: int, data: WorkOrderUpdate):
    """Update a work order (all editable fields)"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        updates = []
        params = []
        for field_name, value in data.model_dump(exclude_none=True).items():
            updates.append(f"{field_name} = ?")
            params.append(value)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(wo_id)

        await db.execute(
            f"UPDATE work_orders SET {', '.join(updates)} WHERE id = ?",
            params
        )
        await db.commit()

        # Return updated work order
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT wo.*, c.name as customer_name
            FROM work_orders wo
            LEFT JOIN customers c ON wo.customer_id = c.id
            WHERE wo.id = ?
        """, (wo_id,))
        row = await cursor.fetchone()
        if not row:
            return {"success": True, "message": f"Work order {wo_id} updated"}
        return dict(row)


@router.delete("/{wo_id}")
async def delete_work_order(wo_id: int):
    """Delete a work order and its items."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Check existence
        cursor = await db.execute("SELECT id FROM work_orders WHERE id = ?", (wo_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Work order not found")

        # Delete items first, then work order
        await db.execute("DELETE FROM work_order_items WHERE work_order_id = ?", (wo_id,))
        await db.execute("DELETE FROM work_orders WHERE id = ?", (wo_id,))
        await db.commit()

        return {"status": "ok"}


@router.post("/{wo_id}/items/{item_id}/assign")
async def assign_battery_to_station(wo_id: int, item_id: int,
                                     station_id: int):
    """Assign a battery item to a test station"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Verify item belongs to work order
        cursor = await db.execute(
            "SELECT id FROM work_order_items WHERE id = ? AND work_order_id = ?",
            (item_id, wo_id)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Item not found")

        # Check station is available
        cursor = await db.execute(
            "SELECT state FROM station_status WHERE station_id = ?",
            (station_id,)
        )
        station = await cursor.fetchone()
        if not station or station[0] != 'idle':
            raise HTTPException(status_code=400,
                              detail=f"Station {station_id} is not available")

        # Assign
        await db.execute("""
            UPDATE work_order_items
            SET current_station_id = ?, status = 'testing',
                testing_started_at = ?
            WHERE id = ?
        """, (station_id, datetime.now().isoformat(), item_id))

        await db.execute("""
            UPDATE station_status
            SET current_work_order_item_id = ?, state = 'testing',
                state_since = ?, updated_at = ?
            WHERE station_id = ?
        """, (item_id, datetime.now().isoformat(),
              datetime.now().isoformat(), station_id))

        await db.commit()

        return {"success": True, "message": f"Item assigned to station {station_id}"}
