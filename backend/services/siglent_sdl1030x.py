"""
Battery Test Bench - Siglent SDL1030X DC Electronic Load SCPI Driver
Version: 1.2.8

Changelog:
v1.2.8 (2026-02-18): Added calibration SCPI commands from SDL1000X Service Manual (SM_E01A):
                      - cal_clear_voltage/cal_clear_current (CALCLS)
                      - cal_write_data (CALibration:DATA) for linear Y=aX+b adjustment
                      - cal_save (CAL:ST) to persist coefficients to FLASH
                      - set_current_range/set_voltage_range for range selection
v1.2.7 (2026-02-16): Fixed SCPI commands from SDL1000X Programming Guide (E02B):
                      - FUNCtion uses CURRent/VOLTage/POWer/RESistance (not CC/CV/CR/CP)
                      - UVP uses VOLTage:LEVel:ON (Von breakover), not VOLTage:PROTection
                      - OCP/OPP use :PROTection:STATe ON + :PROTection:LEVel <value>
                      - Added battery test mode, Ah measurement, Von latch
v1.2.1 (2026-02-16): Initial Siglent SDL1030X driver for service shop model

Siglent SDL1030X: 150V/30A/300W programmable DC electronic load
SCPI interface over TCP port 5025

Reference: SDL1000X Programming Guide E02B, SDL1000X Service Manual SM_E01A
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Mode name mapping (short -> SCPI keyword per SDL1000X manual)
_MODE_MAP = {
    'CC': 'CURRent',
    'CV': 'VOLTage',
    'CR': 'RESistance',
    'CP': 'POWer',
    'LED': 'LED',
}


class SiglentSDL1030X:
    """
    SCPI driver for Siglent SDL1030X programmable DC electronic load.
    Used for battery discharge/capacity testing.

    SCPI commands verified against SDL1000X Programming Guide E02B.
    """

    def __init__(self, ip: str, port: int = 5025, timeout: float = 2.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> bool:
        """Connect to the DC Load via TCP"""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=self.timeout
            )
            self._connected = True
            idn = await self.query("*IDN?")
            logger.info(f"Connected to Load {self.ip}: {idn}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Load {self.ip}: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from the DC Load"""
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._connected = False

    async def _send(self, command: str):
        """Send a SCPI command"""
        if not self._connected or not self._writer:
            raise ConnectionError(f"Load {self.ip} not connected")
        async with self._lock:
            self._writer.write(f"{command}\n".encode())
            await self._writer.drain()

    async def query(self, command: str) -> str:
        """Send a SCPI query and read response"""
        if not self._connected or not self._writer or not self._reader:
            raise ConnectionError(f"Load {self.ip} not connected")
        async with self._lock:
            self._writer.write(f"{command}\n".encode())
            await self._writer.drain()
            response = await asyncio.wait_for(
                self._reader.readline(),
                timeout=self.timeout
            )
            return response.decode().strip()

    # -- Input Control --
    # Manual: [:SOURce]:INPut[:STATe] {ON | OFF | 0 | 1}

    async def input_on(self):
        """Enable load input (start sinking current)"""
        await self._send(":SOURce:INPut:STATe ON")
        logger.info(f"Load {self.ip}: Input ON")

    async def input_off(self):
        """Disable load input (safe state)"""
        await self._send(":SOURce:INPut:STATe OFF")
        logger.info(f"Load {self.ip}: Input OFF")

    async def is_input_on(self) -> bool:
        """Query input state"""
        resp = await self.query(":SOURce:INPut:STATe?")
        return resp.strip() in ("ON", "1")

    # -- Mode Selection --
    # Manual: [:SOURce]:FUNCtion {CURRent | VOLTage | POWer | RESistance | LED}

    async def set_mode(self, mode: str):
        """
        Set operating mode:
          'CC' -> CURRent (Constant Current)
          'CV' -> VOLTage (Constant Voltage)
          'CR' -> RESistance (Constant Resistance)
          'CP' -> POWer (Constant Power)
          'LED' -> LED
        """
        mode = mode.upper()
        scpi_mode = _MODE_MAP.get(mode)
        if not scpi_mode:
            raise ValueError(f"Invalid mode: {mode} (use CC, CV, CR, CP, LED)")
        await self._send(f":SOURce:FUNCtion {scpi_mode}")
        logger.debug(f"Load {self.ip}: Mode set to {scpi_mode}")

    async def get_mode(self) -> str:
        """Query current operating mode"""
        return await self.query(":SOURce:FUNCtion?")

    # -- Current Settings (CC Mode) --
    # Manual: [:SOURce]:CURRent[:LEVel][:IMMediate] <value>

    async def set_current(self, amps: float):
        """Set constant current level (0-30A)"""
        if not 0 <= amps <= 30.0:
            raise ValueError(f"Current out of range: {amps}A (0-30A)")
        await self._send(f":SOURce:CURRent:LEVel:IMMediate {amps:.4f}")
        logger.debug(f"Load {self.ip}: Set current {amps:.4f}A")

    async def set_current_ma(self, milliamps: int):
        """Set constant current in milliamps"""
        await self.set_current(milliamps / 1000.0)

    # -- Voltage Settings (CV Mode) --
    # Manual: [:SOURce]:VOLTage[:LEVel][:IMMediate] <value>

    async def set_voltage(self, volts: float):
        """Set constant voltage level for CV mode (0-150V)"""
        if not 0 <= volts <= 150.0:
            raise ValueError(f"Voltage out of range: {volts}V (0-150V)")
        await self._send(f":SOURce:VOLTage:LEVel:IMMediate {volts:.3f}")
        logger.debug(f"Load {self.ip}: Set voltage {volts:.3f}V")

    # -- Breakover Voltage (Von) --
    # Manual: [:SOURce]:VOLTage[:LEVel]:ON <value>
    # This is the under-voltage cutoff: load turns off when voltage drops below Von

    async def set_von_voltage(self, volts: float):
        """Set Von breakover voltage (UVP - load disables when voltage drops below this)"""
        await self._send(f":SOURce:VOLTage:LEVel:ON {volts:.3f}")
        logger.debug(f"Load {self.ip}: Von (UVP) set to {volts:.3f}V")

    async def get_von_voltage(self) -> float:
        """Query Von breakover voltage"""
        resp = await self.query(":SOURce:VOLTage:LEVel:ON?")
        return float(resp)

    async def set_von_latch(self, enabled: bool):
        """Enable/disable Von latch (if latched, input stays off after Von trip)"""
        state = "ON" if enabled else "OFF"
        await self._send(f":SOURce:VOLTage:LATCh:STATe {state}")

    # Backward-compatible alias
    async def set_voltage_protection(self, volts: float):
        """Set under-voltage protection (Von breakover voltage)"""
        await self.set_von_voltage(volts)

    # -- Measurements --
    # Manual: MEASure:VOLTage[:DC]?, MEASure:CURRent[:DC]?, MEASure:POWer[:DC]?

    async def measure_voltage(self) -> float:
        """Measure actual input voltage"""
        resp = await self.query("MEASure:VOLTage:DC?")
        return float(resp)

    async def measure_current(self) -> float:
        """Measure actual input current"""
        resp = await self.query("MEASure:CURRent:DC?")
        return float(resp)

    async def measure_power(self) -> float:
        """Measure input power"""
        resp = await self.query("MEASure:POWer:DC?")
        return float(resp)

    async def measure_resistance(self) -> float:
        """Measure resistance"""
        resp = await self.query("MEASure:RESistance:DC?")
        return float(resp)

    # -- Protection Settings --
    # Manual: [:SOURce]:CURRent:PROTection:STATe + :LEVel + :DELay
    # Manual: [:SOURce]:POWer:PROTection:STATe + :LEVel + :DELay

    async def set_current_protection(self, amps: float, delay_s: float = 0.0):
        """Set over-current protection (OCP) - enables protection, sets level and delay"""
        await self._send(f":SOURce:CURRent:PROTection:LEVel {amps:.3f}")
        if delay_s > 0:
            await self._send(f":SOURce:CURRent:PROTection:DELay {delay_s:.3f}")
        await self._send(":SOURce:CURRent:PROTection:STATe ON")
        logger.debug(f"Load {self.ip}: OCP set to {amps:.3f}A, delay {delay_s:.1f}s")

    async def set_power_protection(self, watts: float, delay_s: float = 0.0):
        """Set over-power protection (OPP) - enables protection, sets level and delay"""
        await self._send(f":SOURce:POWer:PROTection:LEVel {watts:.1f}")
        if delay_s > 0:
            await self._send(f":SOURce:POWer:PROTection:DELay {delay_s:.3f}")
        await self._send(":SOURce:POWer:PROTection:STATe ON")
        logger.debug(f"Load {self.ip}: OPP set to {watts:.1f}W, delay {delay_s:.1f}s")

    async def disable_current_protection(self):
        """Disable OCP"""
        await self._send(":SOURce:CURRent:PROTection:STATe OFF")

    async def disable_power_protection(self):
        """Disable OPP"""
        await self._send(":SOURce:POWer:PROTection:STATe OFF")

    # -- Range Selection --
    # Manual: [:SOURce]:CURRent:IRANGe <value>, [:SOURce]:CURRent:VRANGe <value>

    async def set_current_range(self, amps: float):
        """Set current range. <5A selects 5A range, >=5A selects 30A range."""
        await self._send(f":SOURce:CURRent:IRANGe {amps:.1f}")
        logger.debug(f"Load {self.ip}: Current range set via {amps:.1f}A")

    async def get_current_range(self) -> float:
        """Query current range (returns 5.0 or 30.0)"""
        resp = await self.query(":SOURce:CURRent:IRANGe?")
        return float(resp)

    async def set_voltage_range(self, volts: float):
        """Set voltage range. <36V selects 36V range, >=36V selects 150V range."""
        await self._send(f":SOURce:CURRent:VRANGe {volts:.1f}")
        logger.debug(f"Load {self.ip}: Voltage range set via {volts:.1f}V")

    async def get_voltage_range(self) -> float:
        """Query voltage range (returns 36.0 or 150.0)"""
        resp = await self.query(":SOURce:CURRent:VRANGe?")
        return float(resp)

    # -- Calibration Commands (SM_E01A Chapter 3) --
    # Linear calibration: Y = aX + b using two test points
    # SCPI: CALCLS:VOLTage, CALCLS:CURRent — clear coefficients
    # SCPI: CALibration:DATA <NR1>,<NR2>,<NR3> — write a,b coefficients
    # SCPI: CAL:ST — save to FLASH

    async def cal_clear_voltage(self):
        """Clear voltage calibration coefficients (a and b) to defaults.
        SM_E01A: CALCLS:VOLTage"""
        await self._send("CALCLS:VOLTage")
        logger.warning(f"Load {self.ip}: Voltage calibration coefficients CLEARED")

    async def cal_clear_current(self):
        """Clear current calibration coefficients (a and b) to defaults.
        SM_E01A: CALCLS:CURRent"""
        await self._send("CALCLS:CURRent")
        logger.warning(f"Load {self.ip}: Current calibration coefficients CLEARED")

    async def cal_write_data(self, nr1: int, step: float, offset: float):
        """Write calibration coefficient pair.
        SM_E01A: CALibration:DATA <NR1>, <NR2>, <NR3>

        NR1: 1 = setting calibration, 2 = readback calibration
        NR2: 'a' step value (linear coefficient)
        NR3: 'b' offset value

        Formulas from SM_E01A Ch.3:
          ctrl_step   = (y2-y1) / (ctrl_x2 - ctrl_x1)
          ctrl_offset = ctrl_x1 - (y1/ctrl_step) + fixed_offset
          meas_step   = (y2-y1) / (meas_x2 - meas_x1)
          meas_offset = meas_x1 - (y1/meas_step)

        Fixed offsets per range (voltage): 1500 (150V), 2000 (36V)
        Fixed offsets per range (current): 500 (30A), 30000 (5A)
        """
        if nr1 not in (1, 2):
            raise ValueError(f"NR1 must be 1 (setting) or 2 (readback), got {nr1}")
        await self._send(f"CALibration:DATA {nr1},{step},{offset}")
        cal_type = "setting" if nr1 == 1 else "readback"
        logger.info(f"Load {self.ip}: Cal data written ({cal_type}): step={step}, offset={offset}")

    async def cal_save(self):
        """Save calibration coefficients to FLASH memory.
        SM_E01A: CAL:ST"""
        await self._send("CAL:ST")
        logger.info(f"Load {self.ip}: Calibration saved to FLASH")

    @staticmethod
    def cal_compute_coefficients(
        set1: float, actual1: float, readback1: float,
        set2: float, actual2: float, readback2: float,
        v_range: float, fixed_offset: float
    ) -> dict:
        """Compute calibration coefficients from two test points.

        Args:
            set1, set2: Instrument set values at point 1 and 2
            actual1, actual2: External DMM measured values at point 1 and 2
            readback1, readback2: Instrument readback values at point 1 and 2
            v_range: Full scale range (36 or 150 for voltage, 5 or 30 for current)
            fixed_offset: Range-specific offset from SM (voltage: 1500/2000, current: 500/30000)

        Returns: dict with ctrl_step, ctrl_offset, meas_step, meas_offset
        """
        ctrl_x1 = (65536 * set1) / v_range
        ctrl_x2 = (65536 * set2) / v_range
        meas_x1 = (65536 * readback1) / v_range
        meas_x2 = (65536 * readback2) / v_range

        ctrl_step = (actual2 - actual1) / (ctrl_x2 - ctrl_x1)
        ctrl_offset = ctrl_x1 - (actual1 / ctrl_step) + fixed_offset

        meas_step = (actual2 - actual1) / (meas_x2 - meas_x1)
        meas_offset = meas_x1 - (actual1 / meas_step)

        return {
            "ctrl_step": ctrl_step,
            "ctrl_offset": ctrl_offset,
            "meas_step": meas_step,
            "meas_offset": meas_offset,
        }

    # -- Error Handling --

    async def query_errors(self) -> Optional[str]:
        """Query error queue"""
        resp = await self.query("SYSTem:ERRor?")
        if resp and not resp.startswith("0,") and not resp.startswith("+0,"):
            return resp
        return None

    async def reset(self):
        """Reset load to default state"""
        await self._send("*RST")
        logger.info(f"Load {self.ip}: Reset")

    async def clear_status(self):
        """Clear status registers"""
        await self._send("*CLS")

    # -- Convenience Methods --

    async def configure_cc_discharge(self, current_a: float, uvp_voltage_v: float):
        """Configure for constant-current discharge with voltage floor (Von)"""
        await self.set_mode('CC')
        await self.set_current(current_a)
        await self.set_von_voltage(uvp_voltage_v)
        await self.set_von_latch(True)

    async def safe_shutdown(self):
        """Emergency shutdown - disable input and disconnect"""
        try:
            await self.input_off()
        except Exception as e:
            logger.error(f"Load {self.ip}: Failed to disable input: {e}")
        await self.disconnect()

    @property
    def connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        return f"SiglentSDL1030X({self.ip}:{self.port}, connected={self._connected})"
