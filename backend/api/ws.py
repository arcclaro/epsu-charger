"""
Battery Test Bench - WebSocket API
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Added task_awaiting_input broadcast for manual task
                      notifications from TaskExecutionOrchestrator
v1.0.1 (2026-02-12): Initial WebSocket endpoint for live updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
import logging
from services import station_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time station updates
    Sends station data every 5 seconds to all connected clients
    """
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")

    try:
        # Send initial station data
        stations = await station_manager.get_all_stations()
        await websocket.send_json({
            "type": "initial",
            "data": [station.model_dump(mode='json') for station in stations]
        })

        # Keep connection alive and send updates
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # No message received, send station update
                stations = await station_manager.get_all_stations()
                await websocket.send_json({
                    "type": "update",
                    "data": [station.model_dump(mode='json') for station in stations]
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"WebSocket client removed. Total connections: {len(active_connections)}")


async def broadcast_station_update(station_id: int, station_data: dict):
    """
    Broadcast a station update to all connected clients
    Called by station_manager when a station state changes
    """
    if not active_connections:
        return

    message = json.dumps({
        "type": "station_update",
        "station_id": station_id,
        "data": station_data
    })

    # Send to all connected clients
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            disconnected.add(connection)

    # Remove disconnected clients
    active_connections.difference_update(disconnected)


async def broadcast_alert(message: str, severity: str = "info"):
    """
    Broadcast a system alert to all connected clients
    severity: "info", "warning", "error"
    """
    if not active_connections:
        return

    alert_message = json.dumps({
        "type": "alert",
        "severity": severity,
        "message": message
    })

    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_text(alert_message)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            disconnected.add(connection)

    active_connections.difference_update(disconnected)


async def broadcast_task_awaiting_input(station_id: int, task_data: dict):
    """
    Broadcast when a manual task needs technician input.
    The PWA uses this to show the appropriate input form.
    """
    if not active_connections:
        return

    message = json.dumps({
        "type": "task_awaiting_input",
        "station_id": station_id,
        "data": task_data
    })

    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send task_awaiting_input: {e}")
            disconnected.add(connection)

    active_connections.difference_update(disconnected)
