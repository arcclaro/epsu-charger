"""
Battery Test Bench - Recipe Engine Service
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial recipe execution engine
"""

import asyncio
import logging
from typing import Optional
from models.recipe import Recipe, RecipeStep, StepType, StopCondition
from services import psu_controller, load_controller
from datetime import datetime

logger = logging.getLogger(__name__)


class RecipeEngine:
    """Executes multi-step test recipes"""

    def __init__(self):
        self.active_recipes = {}  # station_id -> RecipeExecution

    async def start_recipe(self, station_id: int, recipe: Recipe, session_id: int):
        """Start recipe execution on a station"""
        if station_id in self.active_recipes:
            raise ValueError(f"Recipe already running on station {station_id}")

        execution = RecipeExecution(station_id, recipe, session_id)
        self.active_recipes[station_id] = execution

        # Start execution in background
        asyncio.create_task(execution.run())

    async def stop_recipe(self, station_id: int):
        """Stop recipe execution"""
        if station_id in self.active_recipes:
            execution = self.active_recipes[station_id]
            await execution.stop()
            del self.active_recipes[station_id]


class RecipeExecution:
    """Manages execution of a recipe on a station"""

    def __init__(self, station_id: int, recipe: Recipe, session_id: int):
        self.station_id = station_id
        self.recipe = recipe
        self.session_id = session_id
        self.current_step = 0
        self.running = False
        self.step_start_time = None

    async def run(self):
        """Execute recipe steps sequentially"""
        self.running = True
        logger.info(f"Station {self.station_id}: Starting recipe '{self.recipe.name}'")

        try:
            for step_num, step in enumerate(self.recipe.steps, start=1):
                if not self.running:
                    break

                self.current_step = step_num
                await self._execute_step(step)

            logger.info(f"Station {self.station_id}: Recipe complete")

        except Exception as e:
            logger.error(f"Station {self.station_id}: Recipe failed: {e}")
        finally:
            self.running = False
            # Ensure outputs are disabled
            await psu_controller.disable(self.station_id)
            await load_controller.disable(self.station_id)

    async def _execute_step(self, step: RecipeStep):
        """Execute a single recipe step"""
        logger.info(f"Station {self.station_id}: Step {step.step_number} - {step.step_type}")
        self.step_start_time = datetime.now()

        if step.step_type == StepType.CHARGE:
            await self._execute_charge(step)
        elif step.step_type == StepType.DISCHARGE:
            await self._execute_discharge(step)
        elif step.step_type == StepType.REST:
            await self._execute_rest(step)
        elif step.step_type == StepType.WAIT_TEMP:
            await self._execute_wait_temp(step)

    async def _execute_charge(self, step: RecipeStep):
        """Execute charge step"""
        await psu_controller.set_output(
            self.station_id,
            voltage_mv=step.voltage_mv,
            current_ma=step.current_ma
        )

        # Wait for stop condition
        while self.running:
            # Check stop condition
            # TODO: Implement voltage/current/time checks
            await asyncio.sleep(1.0)

            # Check max time
            if step.max_time_s:
                elapsed = (datetime.now() - self.step_start_time).total_seconds()
                if elapsed >= step.max_time_s:
                    logger.info(f"Station {self.station_id}: Step timeout")
                    break

    async def _execute_discharge(self, step: RecipeStep):
        """Execute discharge step"""
        await load_controller.set_load(
            self.station_id,
            current_ma=step.current_ma
        )

        # Wait for stop condition
        while self.running:
            # TODO: Implement voltage/current/time checks
            await asyncio.sleep(1.0)

            # Check max time
            if step.max_time_s:
                elapsed = (datetime.now() - self.step_start_time).total_seconds()
                if elapsed >= step.max_time_s:
                    logger.info(f"Station {self.station_id}: Step timeout")
                    break

    async def _execute_rest(self, step: RecipeStep):
        """Execute rest step (no output)"""
        await psu_controller.disable(self.station_id)
        await load_controller.disable(self.station_id)

        # Wait for time
        await asyncio.sleep(step.stop_value)

    async def _execute_wait_temp(self, step: RecipeStep):
        """Execute wait for temperature step"""
        # TODO: Implement temperature waiting
        await asyncio.sleep(1.0)

    async def stop(self):
        """Stop recipe execution"""
        self.running = False
        await psu_controller.disable(self.station_id)
        await load_controller.disable(self.station_id)


# Singleton instance
_engine = RecipeEngine()


async def start_recipe(station_id: int, recipe: Recipe, session_id: int):
    """Start recipe"""
    await _engine.start_recipe(station_id, recipe, session_id)


async def stop_recipe(station_id: int):
    """Stop recipe"""
    await _engine.stop_recipe(station_id)
