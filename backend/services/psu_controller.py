"""
Battery Test Bench - PSU Controller Service
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial PSU controller with SCPI
"""

import asyncio
import logging
from typing import Optional
from config import settings, get_psu_ip

logger = logging.getLogger(__name__)


class PSUController:
    """Controls SCPI-capable power supplies via TCP"""

    def __init__(self):
        self.connections = {}  # station_id -> (reader, writer)

    async def _get_connection(self, station_id: int):
        """Get or create TCP connection to PSU"""
        if station_id in self.connections:
            return self.connections[station_id]

        ip = get_psu_ip(station_id)
        try:
            reader, writer = await asyncio.open_connection(ip, settings.SCPI_PORT)
            self.connections[station_id] = (reader, writer)
            logger.info(f"Connected to PSU #{station_id} at {ip}")
            return reader, writer
        except Exception as e:
            logger.error(f"Failed to connect to PSU #{station_id} at {ip}: {e}")
            raise

    async def _send_command(self, station_id: int, command: str) -> Optional[str]:
        """Send SCPI command and optionally read response"""
        try:
            reader, writer = await self._get_connection(station_id)

            # Send command
            writer.write(f"{command}\n".encode())
            await writer.drain()

            # If query (ends with ?), read response
            if command.strip().endswith('?'):
                response = await asyncio.wait_for(reader.readline(), timeout=settings.SCPI_TIMEOUT)
                return response.decode().strip()

            return None

        except Exception as e:
            logger.error(f"PSU #{station_id} command failed: {command} - {e}")
            # Close connection on error
            if station_id in self.connections:
                _, writer = self.connections[station_id]
                writer.close()
                await writer.wait_closed()
                del self.connections[station_id]
            raise

    async def set_output(self, station_id: int, voltage_mv: int, current_ma: int):
        """Set PSU output voltage and current limit"""
        voltage_v = voltage_mv / 1000.0
        current_a = current_ma / 1000.0

        logger.info(f"PSU #{station_id}: Setting {voltage_v}V, {current_a}A")

        await self._send_command(station_id, f"VOLT {voltage_v}")
        await self._send_command(station_id, f"CURR {current_a}")
        await self._send_command(station_id, "OUTP ON")

    async def disable(self, station_id: int):
        """Disable PSU output"""
        logger.info(f"PSU #{station_id}: Disabling output")
        await self._send_command(station_id, "OUTP OFF")

    async def read_voltage(self, station_id: int) -> Optional[int]:
        """Read actual output voltage in mV"""
        try:
            response = await self._send_command(station_id, "MEAS:VOLT?")
            if response:
                voltage_v = float(response)
                return int(voltage_v * 1000)
        except Exception as e:
            logger.error(f"Failed to read voltage from PSU #{station_id}: {e}")
        return None

    async def read_current(self, station_id: int) -> Optional[int]:
        """Read actual output current in mA"""
        try:
            response = await self._send_command(station_id, "MEAS:CURR?")
            if response:
                current_a = float(response)
                return int(current_a * 1000)
        except Exception as e:
            logger.error(f"Failed to read current from PSU #{station_id}: {e}")
        return None

    async def identify(self, station_id: int) -> Optional[str]:
        """Identify PSU (get *IDN?)"""
        return await self._send_command(station_id, "*IDN?")


# Singleton instance
_controller = PSUController()


async def set_output(station_id: int, voltage_mv: int, current_ma: int):
    """Set PSU output"""
    await _controller.set_output(station_id, voltage_mv, current_ma)


async def disable(station_id: int):
    """Disable PSU"""
    await _controller.disable(station_id)


async def read_voltage(station_id: int) -> Optional[int]:
    """Read voltage"""
    return await _controller.read_voltage(station_id)


async def read_current(station_id: int) -> Optional[int]:
    """Read current"""
    return await _controller.read_current(station_id)
