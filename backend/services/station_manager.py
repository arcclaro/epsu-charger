"""
Battery Test Bench - Station Manager Service
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Integrated TaskExecutionOrchestrator for per-step procedure
                      execution; start_recipe delegates to orchestrator; station
                      status includes current job_task label
v1.2.7 (2026-02-16): Fix discharge_current_ma → cap_test_discharge_current_ma
v1.2.5 (2026-02-16): Support wait command; fix BatteryConfig field references;
                      discharge with voltage_min_mv; validate against EEPROM limits
v1.0.1 (2026-02-12): Initial station manager with state machines
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
from models.station import StationStatus, StationState, ManualControlCommand, RecipeStartCommand, BatteryConfig
from services import i2c_poller, psu_controller, load_controller, eeprom_manager
from api import ws

logger = logging.getLogger(__name__)


class StationStateMachine:
    """State machine for a single station"""

    def __init__(self, station_id: int):
        self.station_id = station_id
        self.state = StationState.EMPTY
        self.battery_config: Optional[BatteryConfig] = None
        self.error_message: Optional[str] = None
        self.session_id: Optional[int] = None
        self.recipe_name: Optional[str] = None
        self.recipe_step: Optional[int] = None
        self.step_start_time: Optional[datetime] = None
        self.current_task_label: Optional[str] = None
        self.work_job_id: Optional[int] = None

    async def update(self, i2c_data: Dict):
        """Update state machine based on I2C data"""
        if not i2c_data:
            # No I2C data - station offline
            if self.state != StationState.EMPTY:
                await self._transition_to(StationState.EMPTY)
            return

        temp_valid = i2c_data.get("temp_valid", False)
        eeprom_present = i2c_data.get("eeprom_present", False)
        dock_changed = i2c_data.get("dock_changed", False)

        # State transitions
        if self.state == StationState.EMPTY:
            if eeprom_present and temp_valid:
                await self._transition_to(StationState.DOCK_DETECTED)

        elif self.state == StationState.DOCK_DETECTED:
            if not eeprom_present:
                await self._transition_to(StationState.EMPTY)
            elif temp_valid:
                # Load battery config
                self.battery_config = await eeprom_manager.read_battery_config(self.station_id)
                if self.battery_config:
                    await self._transition_to(StationState.READY)

        elif self.state == StationState.READY:
            if not eeprom_present or not temp_valid:
                await self._transition_to(StationState.EMPTY)
                self.battery_config = None

        elif self.state == StationState.RUNNING:
            if not eeprom_present or not temp_valid:
                # Critical error - lost battery or temperature
                self.error_message = "Lost battery dock or temperature sensor"
                await self._emergency_stop()
                await self._transition_to(StationState.ERROR)

        elif self.state == StationState.ERROR:
            if not eeprom_present:
                await self._transition_to(StationState.EMPTY)

    async def _transition_to(self, new_state: StationState):
        """Transition to a new state"""
        if new_state == self.state:
            return

        logger.info(f"Station {self.station_id}: {self.state} -> {new_state}")
        self.state = new_state

        # Broadcast state change via WebSocket
        status = await self.get_status()
        await ws.broadcast_station_update(self.station_id, status.model_dump(mode='json'))

    async def _emergency_stop(self):
        """Emergency stop - disable PSU and load immediately"""
        await psu_controller.disable(self.station_id)
        await load_controller.disable(self.station_id)

    async def get_status(self) -> StationStatus:
        """Get current station status"""
        i2c_data = i2c_poller.get_station_data(self.station_id)

        elapsed_time = None
        if self.step_start_time:
            elapsed_time = (datetime.now() - self.step_start_time).total_seconds()

        # Get current V/I from PSU or Load
        voltage_mv = None
        current_ma = None
        if self.state == StationState.RUNNING:
            voltage_mv = await psu_controller.read_voltage(self.station_id)
            current_ma = await psu_controller.read_current(self.station_id)

        return StationStatus(
            station_id=self.station_id,
            state=self.state,
            temperature_c=i2c_data.get("temperature_c") if i2c_data else None,
            voltage_mv=voltage_mv,
            current_ma=current_ma,
            eeprom_present=i2c_data.get("eeprom_present", False) if i2c_data else False,
            temperature_valid=i2c_data.get("temp_valid", False) if i2c_data else False,
            error_message=self.error_message,
            session_id=self.session_id,
            recipe_name=self.recipe_name,
            recipe_step=self.recipe_step,
            elapsed_time_s=elapsed_time,
            battery_config=self.battery_config
        )


class StationManager:
    """Manages all 12 station state machines"""

    def __init__(self):
        self.stations: Dict[int, StationStateMachine] = {
            i: StationStateMachine(i) for i in range(1, 13)
        }

    async def start_manager(self):
        """Start station manager loop"""
        logger.info("Starting station manager")

        while True:
            # Update all stations
            for station_id, machine in self.stations.items():
                i2c_data = i2c_poller.get_station_data(station_id)
                await machine.update(i2c_data)

            await asyncio.sleep(1.0)  # Update at 1 Hz

    async def get_all_stations(self) -> List[StationStatus]:
        """Get status of all stations"""
        statuses = []
        for station_id in range(1, 13):
            status = await self.stations[station_id].get_status()
            statuses.append(status)
        return statuses

    async def get_station(self, station_id: int) -> Optional[StationStatus]:
        """Get status of a specific station"""
        if station_id not in self.stations:
            return None
        return await self.stations[station_id].get_status()

    async def manual_control(self, command: ManualControlCommand) -> str:
        """Execute manual control command (charge/discharge/wait/stop)"""
        machine = self.stations[command.station_id]

        if command.command == "stop":
            await psu_controller.disable(command.station_id)
            await load_controller.disable(command.station_id)
            machine.step_start_time = None
            if machine.state == StationState.RUNNING:
                await machine._transition_to(StationState.READY)
            return "Stopped"

        if machine.state not in [StationState.READY, StationState.RUNNING]:
            raise ValueError(f"Station {command.station_id} not ready for control")

        # Validate against EEPROM limits
        cfg = machine.battery_config
        if cfg:
            if command.voltage_mv and command.voltage_mv > cfg.charge_voltage_limit_mv:
                raise ValueError(
                    f"Voltage {command.voltage_mv}mV exceeds EEPROM limit "
                    f"{cfg.charge_voltage_limit_mv}mV"
                )
            if command.current_ma and command.current_ma > max(
                cfg.standard_charge_current_ma,
                cfg.cap_test_discharge_current_ma,
                cfg.fast_discharge_current_ma,
            ):
                raise ValueError(
                    f"Current {command.current_ma}mA exceeds EEPROM limits"
                )

        if command.command == "charge":
            if not command.voltage_mv or not command.current_ma:
                raise ValueError("Charge requires voltage_mv and current_ma")
            await load_controller.disable(command.station_id)
            await psu_controller.set_output(
                command.station_id,
                voltage_mv=command.voltage_mv,
                current_ma=command.current_ma,
            )
            machine.step_start_time = datetime.now()
            await machine._transition_to(StationState.RUNNING)
            return f"Charging at {command.current_ma}mA / {command.voltage_mv}mV limit"

        elif command.command == "discharge":
            if not command.current_ma:
                raise ValueError("Discharge requires current_ma")
            await psu_controller.disable(command.station_id)
            await load_controller.set_load(
                command.station_id,
                current_ma=command.current_ma,
                voltage_min_mv=command.voltage_min_mv,
            )
            machine.step_start_time = datetime.now()
            await machine._transition_to(StationState.RUNNING)
            return f"Discharging at {command.current_ma}mA, end voltage {command.voltage_min_mv}mV"

        elif command.command == "wait":
            await psu_controller.disable(command.station_id)
            await load_controller.disable(command.station_id)
            machine.step_start_time = datetime.now()
            await machine._transition_to(StationState.RUNNING)
            duration = command.duration_min or 60
            return f"Timed wait started ({duration} minutes)"

        else:
            raise ValueError(f"Unknown command: {command.command}")

    async def start_recipe(self, command: RecipeStartCommand) -> int:
        """Start a recipe/procedure test via TaskExecutionOrchestrator"""
        machine = self.stations[command.station_id]

        if machine.state != StationState.READY:
            raise ValueError(f"Station {command.station_id} not ready")

        machine.recipe_name = f"Recipe {command.recipe_id}"
        machine.recipe_step = 0
        machine.step_start_time = datetime.now()
        await machine._transition_to(StationState.RUNNING)

        # If a work_job_id is provided, execute via orchestrator
        work_job_id = getattr(command, 'work_job_id', None)
        if work_job_id:
            from services import task_orchestrator
            machine.work_job_id = work_job_id
            await task_orchestrator.execute_job(work_job_id, command.station_id)
            return work_job_id

        return 1  # Fallback session ID for legacy callers

    async def stop_station(self, station_id: int):
        """Stop a station"""
        machine = self.stations[station_id]
        await psu_controller.disable(station_id)
        await load_controller.disable(station_id)
        if machine.state == StationState.RUNNING:
            await machine._transition_to(StationState.READY)

    async def reset_station(self, station_id: int):
        """Reset a station (clear error)"""
        machine = self.stations[station_id]
        if machine.state == StationState.ERROR:
            machine.error_message = None
            await machine._transition_to(StationState.EMPTY)

    async def read_eeprom(self, station_id: int) -> Optional[BatteryConfig]:
        """Read EEPROM config"""
        return await eeprom_manager.read_battery_config(station_id)


# Singleton instance
_manager = StationManager()


async def start_manager():
    """Start the station manager"""
    await _manager.start_manager()


async def get_all_stations() -> List[StationStatus]:
    """Get all stations"""
    return await _manager.get_all_stations()


async def get_station(station_id: int) -> Optional[StationStatus]:
    """Get a station"""
    return await _manager.get_station(station_id)


async def manual_control(command: ManualControlCommand) -> str:
    """Manual control"""
    return await _manager.manual_control(command)


async def start_recipe(command: RecipeStartCommand) -> int:
    """Start recipe"""
    return await _manager.start_recipe(command)


async def stop_station(station_id: int):
    """Stop station"""
    await _manager.stop_station(station_id)


async def reset_station(station_id: int):
    """Reset station"""
    await _manager.reset_station(station_id)


async def read_eeprom(station_id: int) -> Optional[BatteryConfig]:
    """Read EEPROM"""
    return await _manager.read_eeprom(station_id)
