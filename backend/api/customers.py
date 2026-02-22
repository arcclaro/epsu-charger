"""
Battery Test Bench - Customer API Endpoints
Version: 1.2.1

Changelog:
v1.2.1 (2026-02-16): Initial customer CRUD for service shop model
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import aiosqlite
import logging

from config import settings

router = APIRouter(prefix="/customers", tags=["customers"])
logger = logging.getLogger(__name__)


class CustomerCreate(BaseModel):
    name: str
    customer_code: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Portugal"
    tax_id: Optional[str] = None
    payment_terms: str = "Net 30"
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_customers(search: Optional[str] = None, limit: int = 100):
    """List all customers, optionally filtered by search term"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if search:
            cursor = await db.execute("""
                SELECT * FROM customers
                WHERE is_active = 1
                  AND (name LIKE ? OR customer_code LIKE ? OR email LIKE ?)
                ORDER BY name LIMIT ?
            """, (f"%{search}%", f"%{search}%", f"%{search}%", limit))
        else:
            cursor = await db.execute(
                "SELECT * FROM customers WHERE is_active = 1 ORDER BY name LIMIT ?",
                (limit,)
            )

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{customer_id}")
async def get_customer(customer_id: int):
    """Get customer details with work order summary"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,)
        )
        customer = await cursor.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Count work orders
        cursor = await db.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'received' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM work_orders WHERE customer_id = ?
        """, (customer_id,))
        wo_stats = await cursor.fetchone()

        result = dict(customer)
        result['work_order_stats'] = dict(wo_stats)
        return result


@router.post("/")
async def create_customer(data: CustomerCreate):
    """Create a new customer"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Auto-generate customer code if not provided
        code = data.customer_code
        if not code:
            cursor = await db.execute("SELECT COUNT(*) FROM customers")
            count = (await cursor.fetchone())[0]
            code = f"CUST-{count + 1:04d}"

        try:
            cursor = await db.execute("""
                INSERT INTO customers
                    (name, customer_code, contact_person, email, phone,
                     address_line1, address_line2, city, state, postal_code,
                     country, tax_id, payment_terms, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.name, code, data.contact_person, data.email, data.phone,
                data.address_line1, data.address_line2, data.city, data.state,
                data.postal_code, data.country, data.tax_id,
                data.payment_terms, data.notes
            ))
            await db.commit()

            return {
                "id": cursor.lastrowid,
                "customer_code": code,
                "message": f"Customer '{data.name}' created"
            }
        except aiosqlite.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail=f"Customer code '{code}' already exists"
            )


@router.put("/{customer_id}")
async def update_customer(customer_id: int, data: CustomerUpdate):
    """Update a customer"""
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
        params.append(customer_id)

        result = await db.execute(
            f"UPDATE customers SET {', '.join(updates)} WHERE id = ?",
            params
        )
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True, "message": f"Customer {customer_id} updated"}


@router.get("/{customer_id}/work-orders")
async def get_customer_work_orders(customer_id: int, limit: int = 50):
    """Get all work orders for a customer"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT wo.*, COUNT(woi.id) as battery_count
            FROM work_orders wo
            LEFT JOIN work_order_items woi ON woi.work_order_id = wo.id
            WHERE wo.customer_id = ?
            GROUP BY wo.id
            ORDER BY wo.received_date DESC LIMIT ?
        """, (customer_id, limit))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{customer_id}/battery-history")
async def get_customer_battery_history(customer_id: int,
                                        serial_number: Optional[str] = None):
    """Get test history for a customer's batteries"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = """
            SELECT tr.*, woi.serial_number, woi.part_number,
                   wo.work_order_number
            FROM test_records tr
            JOIN work_order_items woi ON tr.work_order_item_id = woi.id
            JOIN work_orders wo ON woi.work_order_id = wo.id
            WHERE wo.customer_id = ?
        """
        params = [customer_id]

        if serial_number:
            query += " AND woi.serial_number = ?"
            params.append(serial_number)

        query += " ORDER BY tr.started_at DESC LIMIT 100"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
