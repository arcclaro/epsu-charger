"""
Battery Test Bench - Siglent SPD1168X Power Supply SCPI Driver
Version: 1.2.7

Changelog:
v1.2.7 (2026-02-16): Fixed SCPI commands from SPD1000X User Manual (UM0501X-E02A):
                      - OUTPut uses channel format: OUTPut CH1,ON / OUTPut CH1,OFF
                      - MEASure commands use explicit channel: MEASure:CURRent? CH1
                      - Added SYSTem:STATus? for CC/CV mode detection
                      - Added OVP/OCP protection commands
                      - Added timer function support
v1.2.1 (2026-02-16): Initial Siglent SPD1168X driver for service shop model

Siglent SPD1168X: Single-channel 16V/8A programmable DC power supply
SCPI interface over TCP port 5025

Reference: SPD1000X User Manual UM0501X-E02A
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SiglentSPD1168X:
    """
    SCPI driver for Siglent SPD1168X programmable DC power supply.
    Used for battery charging operations.
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
        """Connect to the PSU via TCP"""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=self.timeout
            )
            self._connected = True
            idn = await self.query("*IDN?")
            logger.info(f"Connected to PSU {self.ip}: {idn}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PSU {self.ip}: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from the PSU"""
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
            raise ConnectionError(f"PSU {self.ip} not connected")
        async with self._lock:
            self._writer.write(f"{command}\n".encode())
            await self._writer.drain()

    async def query(self, command: str) -> str:
        """Send a SCPI query and read response"""
        if not self._connected or not self._writer or not self._reader:
            raise ConnectionError(f"PSU {self.ip} not connected")
        async with self._lock:
            self._writer.write(f"{command}\n".encode())
            await self._writer.drain()
            response = await asyncio.wait_for(
                self._reader.readline(),
                timeout=self.timeout
            )
            return response.decode().strip()

    # -- Output Control --
    # Manual: OUTPut CH1,{ON|OFF}

    async def output_on(self):
        """Enable output"""
        await self._send("OUTPut CH1,ON")
        logger.info(f"PSU {self.ip}: Output ON")

    async def output_off(self):
        """Disable output (safe state)"""
        await self._send("OUTPut CH1,OFF")
        logger.info(f"PSU {self.ip}: Output OFF")

    async def is_output_on(self) -> bool:
        """Query output state"""
        resp = await self.query("OUTPut CH1?")
        return resp.strip().upper() in ("ON", "1")

    # -- Voltage/Current Settings --
    # Manual: CH1:VOLTage <value>, CH1:CURRent <value>

    async def set_voltage(self, volts: float):
        """Set output voltage (0-16V)"""
        if not 0 <= volts <= 16.0:
            raise ValueError(f"Voltage out of range: {volts}V (0-16V)")
        await self._send(f"CH1:VOLTage {volts:.3f}")
        logger.debug(f"PSU {self.ip}: Set voltage {volts:.3f}V")

    async def get_voltage(self) -> float:
        """Query set voltage"""
        resp = await self.query("CH1:VOLTage?")
        return float(resp)

    async def set_current(self, amps: float):
        """Set output current limit (0-8A)"""
        if not 0 <= amps <= 8.0:
            raise ValueError(f"Current out of range: {amps}A (0-8A)")
        await self._send(f"CH1:CURRent {amps:.3f}")
        logger.debug(f"PSU {self.ip}: Set current limit {amps:.3f}A")

    async def get_current(self) -> float:
        """Query set current limit"""
        resp = await self.query("CH1:CURRent?")
        return float(resp)

    async def set_current_ma(self, milliamps: int):
        """Set output current limit in milliamps"""
        await self.set_current(milliamps / 1000.0)

    async def set_output(self, voltage_v: float, current_a: float):
        """Set voltage and current, then enable output"""
        await self.set_voltage(voltage_v)
        await self.set_current(current_a)
        await self.output_on()

    # -- Measurements --
    # Manual: MEASure:CURRent? CH1, MEASure:VOLTage? CH1, MEASure:POWer? CH1

    async def measure_voltage(self) -> float:
        """Measure actual output voltage"""
        resp = await self.query("MEASure:VOLTage? CH1")
        return float(resp)

    async def measure_current(self) -> float:
        """Measure actual output current"""
        resp = await self.query("MEASure:CURRent? CH1")
        return float(resp)

    async def measure_power(self) -> float:
        """Measure output power"""
        resp = await self.query("MEASure:POWer? CH1")
        return float(resp)

    # -- System Status --
    # Manual: SYSTem:STATus? returns bit-encoded status (bit0=CH1 CV/CC mode)

    async def get_regulation_mode(self) -> str:
        """Query whether PSU is in CV or CC regulation mode.
        Returns 'CV' or 'CC' based on SYSTem:STATus? bit 0."""
        resp = await self.query("SYSTem:STATus?")
        status = int(resp, 16) if resp.startswith("0x") else int(resp)
        return "CC" if (status & 0x01) else "CV"

    # -- Over-Voltage Protection (OVP) --
    # Manual: OUTPut:OVP CH1,{ON|OFF}, OUTPut:OVP:VALue CH1,<value>

    async def set_ovp(self, volts: float):
        """Set over-voltage protection level and enable it"""
        await self._send(f"OUTPut:OVP:VALue CH1,{volts:.3f}")
        await self._send("OUTPut:OVP CH1,ON")
        logger.debug(f"PSU {self.ip}: OVP set to {volts:.3f}V")

    async def disable_ovp(self):
        """Disable over-voltage protection"""
        await self._send("OUTPut:OVP CH1,OFF")

    # -- Over-Current Protection (OCP) --
    # Manual: OUTPut:OCP CH1,{ON|OFF}, OUTPut:OCP:VALue CH1,<value>

    async def set_ocp(self, amps: float):
        """Set over-current protection level and enable it"""
        await self._send(f"OUTPut:OCP:VALue CH1,{amps:.3f}")
        await self._send("OUTPut:OCP CH1,ON")
        logger.debug(f"PSU {self.ip}: OCP set to {amps:.3f}A")

    async def disable_ocp(self):
        """Disable over-current protection"""
        await self._send("OUTPut:OCP CH1,OFF")

    # -- Timer Function --
    # Manual: TIMEr CH1,{ON|OFF}, TIMEr:SET CH1,<groups>,<group>,<V>,<A>,<seconds>

    async def set_timer(self, voltage_v: float, current_a: float, duration_s: int):
        """Configure single-step timer: output for duration_s seconds then stop"""
        await self._send(f"TIMEr:SET CH1,1,1,{voltage_v:.3f},{current_a:.3f},{duration_s}")
        logger.debug(f"PSU {self.ip}: Timer set {voltage_v:.3f}V/{current_a:.3f}A for {duration_s}s")

    async def timer_on(self):
        """Start the timer"""
        await self._send("TIMEr CH1,ON")
        logger.info(f"PSU {self.ip}: Timer started")

    async def timer_off(self):
        """Stop the timer"""
        await self._send("TIMEr CH1,OFF")

    # -- Error Handling --

    async def query_errors(self) -> Optional[str]:
        """Query error queue"""
        resp = await self.query("SYSTem:ERRor?")
        if resp and not resp.startswith("0,") and not resp.startswith("+0,"):
            return resp
        return None

    async def reset(self):
        """Reset PSU to default state"""
        await self._send("*RST")
        logger.info(f"PSU {self.ip}: Reset")

    async def clear_status(self):
        """Clear status registers"""
        await self._send("*CLS")

    # -- Convenience Methods --

    async def safe_shutdown(self):
        """Emergency shutdown — disable output and disconnect"""
        try:
            await self.output_off()
        except Exception as e:
            logger.error(f"PSU {self.ip}: Failed to disable output: {e}")
        await self.disconnect()

    @property
    def connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        return f"SiglentSPD1168X({self.ip}:{self.port}, connected={self._connected})"
