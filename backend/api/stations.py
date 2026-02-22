"""
Battery Test Bench - Station Control API
Version: 1.3.0

Changelog:
v1.3.0 (2026-02-22): Added diagnostics endpoint
v1.2.5 (2026-02-16): Manual control supports charge/discharge/wait/stop;
                      validates against EEPROM limits
v1.0.1 (2026-02-12): Initial station control endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.station import StationStatus, ManualControlCommand, RecipeStartCommand
from services import station_manager
from database import get_db, execute_all
import logging

diag_logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[StationStatus])
async def get_all_stations():
    """Get status of all 12 stations"""
    return await station_manager.get_all_stations()


@router.get("/{station_id}", response_model=StationStatus)
async def get_station(station_id: int):
    """Get status of a specific station"""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    status = await station_manager.get_station(station_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    return status


@router.post("/control")
async def manual_control(command: ManualControlCommand):
    """
    Manual control of a station.
    Commands: 'charge', 'discharge', 'wait', 'stop'
    All limits validated against EEPROM battery model parameters.
    """
    if not 1 <= command.station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    try:
        result = await station_manager.manual_control(command)
        return {"success": True, "message": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Control failed: {str(e)}")


@router.post("/start-recipe")
async def start_recipe(command: RecipeStartCommand):
    """Start a recipe test on a station"""
    if not 1 <= command.station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    try:
        session_id = await station_manager.start_recipe(command)
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Recipe started on station {command.station_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recipe: {str(e)}")


@router.post("/{station_id}/stop")
async def stop_station(station_id: int):
    """Stop any active operation on a station"""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    try:
        await station_manager.stop_station(station_id)
        return {"success": True, "message": f"Station {station_id} stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop station: {str(e)}")


@router.post("/{station_id}/reset")
async def reset_station(station_id: int):
    """Reset a station (clears error state)"""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    try:
        await station_manager.reset_station(station_id)
        return {"success": True, "message": f"Station {station_id} reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset station: {str(e)}")


@router.get("/{station_id}/diagnostics")
async def station_diagnostics(station_id: int):
    """Get diagnostics report for a station."""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    report = {
        "station_id": station_id,
        "psu_status": "offline",
        "load_status": "offline",
        "rp2040_status": "offline",
        "temp_sensor_status": "offline",
    }

    # Check PSU
    try:
        from services import psu_controller
        v = await psu_controller.read_voltage(station_id)
        report["psu_status"] = "online" if v is not None else "offline"
    except Exception as e:
        diag_logger.debug(f"PSU diag station {station_id}: {e}")
        report["psu_status"] = "error"

    # Check Load
    try:
        from services import load_controller
        v = await load_controller.read_voltage(station_id)
        report["load_status"] = "online" if v is not None else "offline"
    except Exception as e:
        diag_logger.debug(f"Load diag station {station_id}: {e}")
        report["load_status"] = "error"

    # Check RP2040 / temp sensor via I2C poller
    try:
        from services import i2c_poller
        i2c_data = i2c_poller.get_station_data(station_id)
        if i2c_data:
            report["rp2040_status"] = "online"
            # If temperature data exists, sensor is online
            temp = i2c_data.get("temperature_c")
            if temp is not None and temp > -50:
                report["temp_sensor_status"] = "online"
    except Exception as e:
        diag_logger.debug(f"I2C diag station {station_id}: {e}")

    return report


@router.get("/{station_id}/eeprom")
async def read_eeprom(station_id: int):
    """Read EEPROM configuration from a station"""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")

    try:
        config = await station_manager.read_eeprom(station_id)
        if not config:
            raise HTTPException(status_code=404, detail="No battery dock detected")
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read EEPROM: {str(e)}")
