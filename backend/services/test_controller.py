"""
Battery Test Bench - Station Test Controller (CMM-compliant)
Version: 1.2.7

Changelog:
v1.2.7 (2026-02-16): Comprehensive TestParameters from BatteryConfig v1.2.6;
                      reconditioning charge, fast discharge, pass/fail evaluation,
                      voltage check at time, capacity % check, age-based rest
v1.2.2 (2026-02-16): Removed RP2040 voltage writes — RP2040 is temp+EEPROM only;
                      voltage/current comes exclusively from SCPI equipment
v1.2.1 (2026-02-16): Initial CMM-compliant test controller with safety monitoring

Implements automated capacity test procedure with:
- Mandatory pre-discharge to prevent overcharge accumulation
- Optional reconditioning charge (for batteries stored > threshold)
- 1-second continuous temperature monitoring via RP2040 (MAX31820)
- Voltage/current measurement via Siglent SCPI equipment (not RP2040)
- Age-based rest period (configurable threshold + duration from EEPROM)
- EEPROM-based battery model parameter loading via RP2040 (DS24B33)
- Ampere-hour integration for capacity measurement
- Pass/fail evaluation: min time, min capacity %, voltage check at time
- Optional fast discharge test (e.g., Cobham 301-3017)
- Post-charge for storage/delivery
"""

import asyncio
import logging
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from services.siglent_spd1168x import SiglentSPD1168X
from services.siglent_sdl1030x import SiglentSDL1030X
import xiao_registers as reg

logger = logging.getLogger(__name__)


class TestPhase(str, Enum):
    """Test execution phases"""
    IDLE = "idle"
    PRE_DISCHARGE = "pre_discharge"
    PRE_REST = "pre_rest"
    RECONDITIONING = "reconditioning"
    CHARGING = "charging"
    POST_CHARGE_REST = "post_charge_rest"
    CAP_DISCHARGING = "cap_discharging"
    FAST_DISCHARGE_REST = "fast_discharge_rest"
    FAST_DISCHARGING = "fast_discharging"
    POST_PARTIAL_CHARGE = "post_partial_charge"
    COMPLETE_PASS = "complete_pass"
    COMPLETE_FAIL = "complete_fail"
    ABORTED = "aborted"


class TestType(str, Enum):
    """Available test types"""
    AUTOMATED_CAPACITY = "automated_capacity"
    STANDARD_CHARGE = "standard_charge"
    FAST_CHARGE = "fast_charge"
    TRICKLE_CHARGE = "trickle_charge"
    DISCHARGE_ONLY = "discharge_only"


@dataclass
class TestParameters:
    """
    Computed test parameters from EEPROM BatteryConfig + battery age.
    Built by eeprom_manager.build_test_params_from_eeprom().
    """
    # Standard charge
    charge_current_ma: int
    charge_voltage_limit_mv: int
    charge_duration_min: int
    charge_temp_max_c: float

    # Reconditioning (pre-charge for long-stored batteries)
    needs_reconditioning: bool = False
    recondition_charge_current_ma: int = 0
    recondition_charge_duration_min: int = 0

    # Capacity test discharge
    cap_test_discharge_current_ma: int = 0
    cap_test_end_voltage_mv: int = 5000
    cap_test_max_duration_min: int = 480
    discharge_temp_max_c: float = 55.0

    # Pass/fail criteria
    cap_test_pass_min_minutes: int = 0       # 0 = not used
    cap_test_pass_min_capacity_pct: int = 0  # 0 = not used
    nominal_capacity_mah: int = 0            # For % calculation
    cap_test_voltage_check_time_min: int = 0  # 0 = not used
    cap_test_voltage_check_min_mv: int = 0    # 0 = not used

    # Fast discharge (optional second discharge test)
    fast_discharge_enabled: bool = False
    fast_discharge_current_ma: int = 0
    fast_discharge_end_voltage_mv: int = 0
    fast_discharge_pass_min_minutes: int = 0
    fast_discharge_rest_before_min: int = 60

    # Pre-discharge
    pre_discharge_current_ma: int = 0
    pre_discharge_end_voltage_mv: int = 5000

    # Rest
    rest_before_discharge_min: int = 240

    # Post-charge
    post_charge_enabled: bool = True
    post_charge_duration_min: int = 270

    # Safety
    emergency_temp_max_c: float = 60.0
    min_operating_temp_c: float = -15.0
    absolute_min_voltage_mv: int = 4500


@dataclass
class CapacityResult:
    """Result from a discharge capacity measurement"""
    capacity_ah: float = 0.0
    capacity_mah: float = 0.0
    duration_min: float = 0.0
    max_temp_c: float = 0.0
    end_voltage_mv: float = 0.0
    passed: bool = True
    fail_reason: Optional[str] = None


@dataclass
class TestResult:
    """Result of a completed test"""
    success: bool
    phase: TestPhase
    cap_test_result: Optional[CapacityResult] = None
    fast_discharge_result: Optional[CapacityResult] = None
    duration_sec: float = 0.0
    failure_reason: Optional[str] = None
    abort_reason: Optional[str] = None
    safety_events: int = 0
    thermal_runaway: bool = False


@dataclass
class DataSample:
    """Single data sample during test"""
    timestamp: datetime
    voltage_v: float
    current_a: float
    temp1_c: float
    temp2_c: Optional[float] = None
    phase: str = ""


class SafetyAbortError(Exception):
    """Raised when safety condition triggers abort"""
    pass


class StationTestController:
    """
    Controls automated testing for one station.
    Implements CMM-compliant capacity test with continuous safety monitoring.
    """

    def __init__(self, station_id: int, i2c_bus, psu: SiglentSPD1168X,
                 load: SiglentSDL1030X):
        self.station_id = station_id
        self.i2c_bus = i2c_bus
        self.i2c_addr = 0x20 + station_id - 1
        self.psu = psu
        self.load = load

        self.current_phase = TestPhase.IDLE
        self.phase_start_time: Optional[datetime] = None
        self.test_start_time: Optional[datetime] = None
        self.influx_test_id: Optional[str] = None
        self.abort_requested = False
        self.abort_reason: Optional[str] = None

        self.data_log: List[DataSample] = []
        self._safety_task: Optional[asyncio.Task] = None

    async def run_automated_capacity_test(self, params: TestParameters,
                                           data_callback=None) -> TestResult:
        """
        Execute full CMM-compliant automated capacity test.

        Phases (all driven by EEPROM parameters):
        1. Pre-discharge (drain residual charge to floor voltage)
        2. Pre-rest (1 hour cool-down)
        3. Reconditioning charge (if battery stored > threshold months)
        4. Standard charge (per EEPROM current/voltage/duration)
        5. Post-charge rest (age-based: standard or extended from EEPROM)
        6. Capacity discharge test (with pass/fail evaluation)
        7. Fast discharge test (optional, e.g., Cobham 301-3017)
        8. Post partial charge for storage/delivery

        Safety monitoring runs continuously at 1-second intervals.
        """
        self.influx_test_id = str(uuid.uuid4())
        self.test_start_time = datetime.now()
        self.data_log = []
        self.abort_requested = False
        self.abort_reason = None

        # Start safety monitor in background
        self._safety_task = asyncio.create_task(
            self._safety_monitor_loop(params)
        )

        cap_result = None
        fast_result = None

        try:
            # Phase 1: PRE-DISCHARGE
            await self._set_phase(TestPhase.PRE_DISCHARGE)
            await self._discharge_to_floor(
                current_ma=params.pre_discharge_current_ma,
                voltage_min_mv=params.pre_discharge_end_voltage_mv,
                max_duration_sec=1800,
                temp_max_c=params.discharge_temp_max_c
            )
            self._check_abort()

            # Phase 2: PRE-REST (1 hour cool-down)
            await self._set_phase(TestPhase.PRE_REST)
            await self._rest_period_sec(3600)
            self._check_abort()

            # Phase 3: RECONDITIONING CHARGE (optional)
            if params.needs_reconditioning:
                await self._set_phase(TestPhase.RECONDITIONING)
                await self._charge_battery(
                    current_ma=params.recondition_charge_current_ma,
                    voltage_limit_mv=params.charge_voltage_limit_mv,
                    duration_min=params.recondition_charge_duration_min,
                    temp_max_c=params.charge_temp_max_c
                )
                self._check_abort()

            # Phase 4: STANDARD CHARGE
            await self._set_phase(TestPhase.CHARGING)
            await self._charge_battery(
                current_ma=params.charge_current_ma,
                voltage_limit_mv=params.charge_voltage_limit_mv,
                duration_min=params.charge_duration_min,
                temp_max_c=params.charge_temp_max_c
            )
            self._check_abort()

            # Phase 5: POST-CHARGE REST
            await self._set_phase(TestPhase.POST_CHARGE_REST)
            rest_sec = params.rest_before_discharge_min * 60
            await self._rest_period_sec(rest_sec)
            self._check_abort()

            # Phase 6: CAPACITY DISCHARGE TEST
            await self._set_phase(TestPhase.CAP_DISCHARGING)
            cap_result = await self._discharge_capacity_test(params)
            self._check_abort()

            # Phase 7: FAST DISCHARGE TEST (optional)
            if params.fast_discharge_enabled:
                # Re-charge before fast discharge
                await self._set_phase(TestPhase.CHARGING)
                await self._charge_battery(
                    current_ma=params.charge_current_ma,
                    voltage_limit_mv=params.charge_voltage_limit_mv,
                    duration_min=params.charge_duration_min,
                    temp_max_c=params.charge_temp_max_c
                )
                self._check_abort()

                # Rest before fast discharge
                await self._set_phase(TestPhase.FAST_DISCHARGE_REST)
                fast_rest_sec = params.fast_discharge_rest_before_min * 60
                await self._rest_period_sec(fast_rest_sec)
                self._check_abort()

                # Fast discharge
                await self._set_phase(TestPhase.FAST_DISCHARGING)
                fast_result = await self._fast_discharge_test(params)
                self._check_abort()

            # Phase 8: POST PARTIAL CHARGE FOR STORAGE
            if params.post_charge_enabled:
                await self._set_phase(TestPhase.POST_PARTIAL_CHARGE)
                await self._charge_battery(
                    current_ma=params.charge_current_ma,
                    voltage_limit_mv=params.charge_voltage_limit_mv,
                    duration_min=params.post_charge_duration_min,
                    temp_max_c=params.charge_temp_max_c
                )

            # EVALUATE PASS/FAIL
            overall_pass = True
            fail_reasons = []

            if cap_result and not cap_result.passed:
                overall_pass = False
                fail_reasons.append(f"Cap test: {cap_result.fail_reason}")

            if fast_result and not fast_result.passed:
                overall_pass = False
                fail_reasons.append(f"Fast discharge: {fast_result.fail_reason}")

            final_phase = TestPhase.COMPLETE_PASS if overall_pass else TestPhase.COMPLETE_FAIL
            await self._set_phase(final_phase)
            total_duration = (datetime.now() - self.test_start_time).total_seconds()

            return TestResult(
                success=overall_pass,
                phase=final_phase,
                cap_test_result=cap_result,
                fast_discharge_result=fast_result,
                duration_sec=total_duration,
                failure_reason="; ".join(fail_reasons) if fail_reasons else None,
            )

        except SafetyAbortError as e:
            await self._set_phase(TestPhase.ABORTED)
            return TestResult(
                success=False,
                phase=TestPhase.ABORTED,
                cap_test_result=cap_result,
                fast_discharge_result=fast_result,
                abort_reason=str(e),
                safety_events=1,
                thermal_runaway='runaway' in str(e).lower(),
                duration_sec=(datetime.now() - self.test_start_time).total_seconds()
            )

        except Exception as e:
            logger.error(f"Station {self.station_id}: Test error: {e}")
            await self._set_phase(TestPhase.COMPLETE_FAIL)
            return TestResult(
                success=False,
                phase=TestPhase.COMPLETE_FAIL,
                cap_test_result=cap_result,
                fast_discharge_result=fast_result,
                failure_reason=str(e),
                duration_sec=(datetime.now() - self.test_start_time).total_seconds()
            )

        finally:
            # Always ensure safe state
            await self._safe_shutdown()
            if self._safety_task and not self._safety_task.done():
                self._safety_task.cancel()

    # == Phase Execution Methods ==

    async def _charge_battery(self, current_ma: int, voltage_limit_mv: int,
                               duration_min: int, temp_max_c: float):
        """Execute controlled charging with 1-second monitoring"""
        voltage_v = voltage_limit_mv / 1000.0
        current_a = current_ma / 1000.0

        await self.psu.set_voltage(voltage_v)
        await self.psu.set_current(current_a)
        await self.psu.output_on()

        end_time = datetime.now() + timedelta(minutes=duration_min)

        while datetime.now() < end_time:
            self._check_abort()

            v = await self.psu.measure_voltage()
            i = await self.psu.measure_current()
            temp = await self._read_temperature()

            if temp > temp_max_c:
                await self.psu.output_off()
                raise SafetyAbortError(
                    f"Charge temperature exceeded {temp_max_c}C: {temp:.1f}C"
                )

            self._log_sample(v, i, temp, self.current_phase.value)
            await asyncio.sleep(1.0)

        await self.psu.output_off()

    async def _discharge_capacity_test(self, params: TestParameters) -> CapacityResult:
        """
        Execute capacity discharge with Ah integration and pass/fail evaluation.

        Pass/fail criteria (all from EEPROM, 0 = not used):
        - cap_test_pass_min_minutes: battery must sustain load for at least this long
        - cap_test_pass_min_capacity_pct: measured capacity must be >= this % of nominal
        - cap_test_voltage_check_time_min + cap_test_voltage_check_min_mv:
          voltage must be >= min_mv at the specified time during discharge
        """
        current_a = params.cap_test_discharge_current_ma / 1000.0

        await self.load.set_mode('CC')
        await self.load.set_current(current_a)
        await self.load.set_voltage_protection(params.cap_test_end_voltage_mv / 1000.0)
        await self.load.input_on()

        start_time = datetime.now()
        max_time = start_time + timedelta(minutes=params.cap_test_max_duration_min)
        last_sample = start_time
        ah_integrated = 0.0
        max_temp = -273.15
        voltage_check_done = False
        voltage_check_passed = True
        end_voltage_mv = 0.0

        while datetime.now() < max_time:
            self._check_abort()

            v = await self.load.measure_voltage()
            i = await self.load.measure_current()
            temp = await self._read_temperature()
            max_temp = max(max_temp, temp)
            end_voltage_mv = v * 1000

            elapsed_min = (datetime.now() - start_time).total_seconds() / 60.0

            # Voltage check at specified time
            if (not voltage_check_done
                    and params.cap_test_voltage_check_time_min > 0
                    and elapsed_min >= params.cap_test_voltage_check_time_min):
                voltage_check_done = True
                if v * 1000 < params.cap_test_voltage_check_min_mv:
                    voltage_check_passed = False
                    logger.warning(
                        f"Station {self.station_id}: Voltage check FAIL at "
                        f"{elapsed_min:.1f}min: {v*1000:.0f}mV < "
                        f"{params.cap_test_voltage_check_min_mv}mV"
                    )

            # Check voltage floor (end-of-discharge)
            if v * 1000 <= params.cap_test_end_voltage_mv:
                break

            # Check temperature
            if temp > params.discharge_temp_max_c:
                await self.load.input_off()
                raise SafetyAbortError(
                    f"Discharge temperature exceeded {params.discharge_temp_max_c}C: {temp:.1f}C"
                )

            # Check absolute minimum voltage (cell damage prevention)
            if v * 1000 < params.absolute_min_voltage_mv:
                await self.load.input_off()
                raise SafetyAbortError(
                    f"Voltage below absolute minimum {params.absolute_min_voltage_mv}mV: "
                    f"{v*1000:.0f}mV"
                )

            # Integrate Ah
            now = datetime.now()
            dt_h = (now - last_sample).total_seconds() / 3600.0
            ah_integrated += i * dt_h
            last_sample = now

            self._log_sample(v, i, temp, self.current_phase.value)
            await asyncio.sleep(1.0)

        await self.load.input_off()

        duration_min = (datetime.now() - start_time).total_seconds() / 60.0
        capacity_mah = ah_integrated * 1000

        # Evaluate pass/fail
        passed = True
        fail_reason = None

        # Check 1: Minimum discharge time
        if params.cap_test_pass_min_minutes > 0:
            if duration_min < params.cap_test_pass_min_minutes:
                passed = False
                fail_reason = (f"Discharge time {duration_min:.1f}min < "
                               f"required {params.cap_test_pass_min_minutes}min")

        # Check 2: Minimum capacity percentage
        if params.cap_test_pass_min_capacity_pct > 0 and params.nominal_capacity_mah > 0:
            actual_pct = (capacity_mah / params.nominal_capacity_mah) * 100
            if actual_pct < params.cap_test_pass_min_capacity_pct:
                passed = False
                fail_reason = (f"Capacity {actual_pct:.1f}% < "
                               f"required {params.cap_test_pass_min_capacity_pct}%")

        # Check 3: Voltage at specified time
        if not voltage_check_passed:
            passed = False
            fail_reason = (fail_reason or "") + "Voltage check at time failed"

        return CapacityResult(
            capacity_ah=ah_integrated,
            capacity_mah=capacity_mah,
            duration_min=duration_min,
            max_temp_c=max_temp,
            end_voltage_mv=end_voltage_mv,
            passed=passed,
            fail_reason=fail_reason,
        )

    async def _fast_discharge_test(self, params: TestParameters) -> CapacityResult:
        """
        Execute fast discharge test (e.g., Cobham 301-3017 high-rate test).
        Separate from capacity test — uses higher current, different pass criteria.
        """
        current_a = params.fast_discharge_current_ma / 1000.0

        await self.load.set_mode('CC')
        await self.load.set_current(current_a)
        await self.load.set_voltage_protection(params.fast_discharge_end_voltage_mv / 1000.0)
        await self.load.input_on()

        start_time = datetime.now()
        max_time = start_time + timedelta(minutes=120)  # Safety max 2h
        last_sample = start_time
        ah_integrated = 0.0
        max_temp = -273.15
        end_voltage_mv = 0.0

        while datetime.now() < max_time:
            self._check_abort()

            v = await self.load.measure_voltage()
            i = await self.load.measure_current()
            temp = await self._read_temperature()
            max_temp = max(max_temp, temp)
            end_voltage_mv = v * 1000

            if v * 1000 <= params.fast_discharge_end_voltage_mv:
                break

            if temp > params.discharge_temp_max_c:
                await self.load.input_off()
                raise SafetyAbortError(
                    f"Fast discharge temp exceeded {params.discharge_temp_max_c}C: {temp:.1f}C"
                )

            if v * 1000 < params.absolute_min_voltage_mv:
                await self.load.input_off()
                raise SafetyAbortError(
                    f"Voltage below absolute minimum: {v*1000:.0f}mV"
                )

            now = datetime.now()
            dt_h = (now - last_sample).total_seconds() / 3600.0
            ah_integrated += i * dt_h
            last_sample = now

            self._log_sample(v, i, temp, self.current_phase.value)
            await asyncio.sleep(1.0)

        await self.load.input_off()

        duration_min = (datetime.now() - start_time).total_seconds() / 60.0

        # Pass/fail: must sustain fast discharge for minimum time
        passed = True
        fail_reason = None
        if params.fast_discharge_pass_min_minutes > 0:
            if duration_min < params.fast_discharge_pass_min_minutes:
                passed = False
                fail_reason = (f"Fast discharge {duration_min:.1f}min < "
                               f"required {params.fast_discharge_pass_min_minutes}min")

        return CapacityResult(
            capacity_ah=ah_integrated,
            capacity_mah=ah_integrated * 1000,
            duration_min=duration_min,
            max_temp_c=max_temp,
            end_voltage_mv=end_voltage_mv,
            passed=passed,
            fail_reason=fail_reason,
        )

    async def _discharge_to_floor(self, current_ma: int, voltage_min_mv: int,
                                   max_duration_sec: int, temp_max_c: float):
        """Pre-discharge to voltage floor (non-capacity-measuring)"""
        current_a = current_ma / 1000.0

        await self.load.set_mode('CC')
        await self.load.set_current(current_a)
        await self.load.set_voltage_protection(voltage_min_mv / 1000.0)
        await self.load.input_on()

        end_time = datetime.now() + timedelta(seconds=max_duration_sec)

        while datetime.now() < end_time:
            self._check_abort()

            v = await self.load.measure_voltage()
            temp = await self._read_temperature()

            if v * 1000 <= voltage_min_mv:
                break

            if temp > temp_max_c:
                await self.load.input_off()
                raise SafetyAbortError(
                    f"Pre-discharge temp exceeded {temp_max_c}C: {temp:.1f}C"
                )

            await asyncio.sleep(1.0)

        await self.load.input_off()

    async def _rest_period_sec(self, duration_sec: int):
        """Wait for rest period, checking for abort every 10 seconds"""
        end_time = datetime.now() + timedelta(seconds=duration_sec)
        while datetime.now() < end_time:
            self._check_abort()
            temp = await self._read_temperature()
            self._log_sample(0, 0, temp, self.current_phase.value)
            await asyncio.sleep(10.0)

    # == Safety ==

    async def _safety_monitor_loop(self, params: TestParameters):
        """Background safety monitor — runs continuously during tests"""
        while True:
            try:
                # Read RP2040 safety flags
                status = self.i2c_bus.read_byte_data(self.i2c_addr, reg.REG_STATUS)
                flags = reg.parse_status_flags(status)

                # Check temperature validity
                if not flags['temp_valid'] and self.current_phase not in (
                    TestPhase.IDLE, TestPhase.COMPLETE_PASS,
                    TestPhase.COMPLETE_FAIL, TestPhase.ABORTED
                ):
                    self._request_abort("Temperature sensor lost during test")

                # Check SCPI equipment errors
                psu_err = await self.psu.query_errors()
                if psu_err:
                    logger.warning(f"Station {self.station_id}: PSU error: {psu_err}")

                load_err = await self.load.query_errors()
                if load_err:
                    logger.warning(f"Station {self.station_id}: Load error: {load_err}")

            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(f"Station {self.station_id}: Safety monitor error: {e}")

            await asyncio.sleep(1.0)

    # == Helpers ==

    async def _set_phase(self, phase: TestPhase):
        """Transition to a new test phase"""
        logger.info(f"Station {self.station_id}: {self.current_phase} -> {phase}")
        self.current_phase = phase
        self.phase_start_time = datetime.now()

    async def _read_temperature(self) -> float:
        """Read temperature from RP2040"""
        try:
            raw = self.i2c_bus.read_word_data(self.i2c_addr, reg.REG_TEMP_RAW)
            return reg.parse_temperature(raw)
        except Exception as e:
            logger.error(f"Station {self.station_id}: Temp read failed: {e}")
            return -999.0

    def _log_sample(self, voltage_v: float, current_a: float,
                    temp_c: float, phase: str):
        """Record a data sample"""
        self.data_log.append(DataSample(
            timestamp=datetime.now(),
            voltage_v=voltage_v,
            current_a=current_a,
            temp1_c=temp_c,
            phase=phase
        ))

    def _check_abort(self):
        """Check if abort was requested"""
        if self.abort_requested:
            raise SafetyAbortError(self.abort_reason or "Abort requested")

    def _request_abort(self, reason: str):
        """Request test abort (called from safety monitor)"""
        if not self.abort_requested:
            logger.warning(f"Station {self.station_id}: ABORT - {reason}")
            self.abort_requested = True
            self.abort_reason = reason

    async def _safe_shutdown(self):
        """Ensure all equipment is in safe state"""
        try:
            await self.psu.output_off()
        except Exception as e:
            logger.error(f"Station {self.station_id}: PSU off failed: {e}")
        try:
            await self.load.input_off()
        except Exception as e:
            logger.error(f"Station {self.station_id}: Load off failed: {e}")

    def request_stop(self):
        """External stop request"""
        self._request_abort("User requested stop")

    def get_progress(self) -> dict:
        """Get current test progress"""
        elapsed = 0.0
        if self.test_start_time:
            elapsed = (datetime.now() - self.test_start_time).total_seconds()

        return {
            'station_id': self.station_id,
            'phase': self.current_phase.value,
            'phase_start': self.phase_start_time.isoformat() if self.phase_start_time else None,
            'test_start': self.test_start_time.isoformat() if self.test_start_time else None,
            'elapsed_sec': elapsed,
            'sample_count': len(self.data_log),
            'influx_test_id': self.influx_test_id,
            'abort_requested': self.abort_requested,
            'abort_reason': self.abort_reason
        }
