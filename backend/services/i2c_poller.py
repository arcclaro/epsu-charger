"""
Battery Test Bench - I2C Polling Service
Version: 1.1.1

Changelog:
v1.1.1 (2026-02-12): Updated for corrected register map (EVENT_LOG 0x200→0x30)
v1.0.1 (2026-02-12): Initial I2C poller service
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from config import settings, get_xiao_address
import xiao_registers as reg

try:
    import smbus2
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logging.warning("smbus2 not available - I2C disabled")

logger = logging.getLogger(__name__)


class I2CPoller:
    """Polls all 12 XIAO modules via I2C"""

    def __init__(self):
        self.running = False
        self.bus = None
        self.last_poll = None
        self.station_data: Dict[int, Dict] = {}
        self.error_counts: Dict[int, int] = {i: 0 for i in range(1, 13)}

    async def start_polling(self):
        """Start I2C polling loop"""
        if not I2C_AVAILABLE:
            logger.error("I2C not available - polling disabled")
            return

        logger.info(f"Starting I2C poller on bus {settings.I2C_BUS}")

        try:
            self.bus = smbus2.SMBus(settings.I2C_BUS)
            self.running = True

            while self.running:
                await self._poll_all_stations()
                self.last_poll = datetime.now()
                await asyncio.sleep(settings.I2C_POLL_INTERVAL)

        except Exception as e:
            logger.error(f"I2C poller crashed: {e}")
            self.running = False
        finally:
            if self.bus:
                self.bus.close()

    async def _poll_all_stations(self):
        """Poll all 12 stations"""
        for station_id in range(1, 13):
            try:
                data = await self._poll_station(station_id)
                self.station_data[station_id] = data
                self.error_counts[station_id] = 0  # Reset error count on success
            except Exception as e:
                self.error_counts[station_id] += 1
                if self.error_counts[station_id] <= 3:  # Log first 3 errors only
                    logger.error(f"Failed to poll station {station_id}: {e}")

    async def _poll_station(self, station_id: int) -> Dict:
        """
        Poll a single station via I2C
        Returns dict with status flags, temperature, EEPROM data
        """
        address = get_xiao_address(station_id)

        # Run I2C read in executor to avoid blocking
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._read_i2c_registers, address)

        return data

    def _read_i2c_registers(self, address: int) -> Dict:
        """
        Read I2C registers from XIAO module

        Uses corrected register map (v1.1):
          0x00: Status flags
          0x01: Station ID
          0x02-03: Temperature (12-bit signed, 0.0625°C/LSB)
          0x04-05: EEPROM data length
          0x06: Firmware version
          0x07: Error counter
          0x20: Temperature history (16 bytes)
          0x30: Event log (96 bytes) ⚠️ UPDATED from 0x200
          0x10+: EEPROM buffer (512 bytes)
        """
        if not self.bus:
            raise RuntimeError("I2C bus not initialized")

        # Read status byte
        status = self.bus.read_byte_data(address, reg.REG_STATUS)

        # Parse status flags using helper
        status_flags = reg.parse_status_flags(status)

        # Read temperature using helper
        temp_raw = self.bus.read_word_data(address, reg.REG_TEMP_RAW)
        temperature_c = reg.parse_temperature(temp_raw) if status_flags['temp_valid'] else None

        # Read EEPROM length
        eeprom_len = self.bus.read_word_data(address, reg.REG_EEPROM_LEN)

        # Read firmware version
        fw_version = self.bus.read_byte_data(address, reg.REG_FW_VERSION)

        # Read error counter
        error_count = self.bus.read_byte_data(address, reg.REG_ERROR_COUNT)

        # Read uptime (optional, for diagnostics)
        uptime_ms = None
        try:
            uptime_bytes = self.bus.read_i2c_block_data(address, reg.REG_UPTIME, 4)
            uptime_ms = int.from_bytes(uptime_bytes, 'little')
        except Exception:
            pass  # Non-critical

        # Read temperature history (optional)
        temp_history = None
        try:
            temp_history_raw = self.bus.read_i2c_block_data(address, reg.REG_TEMP_HISTORY, 16)
            temp_history = []
            for i in range(8):
                raw = (temp_history_raw[i*2+1] << 8) | temp_history_raw[i*2]
                temp_history.append(reg.parse_temperature(raw))
        except Exception as e:
            logger.debug(f"Failed to read temp history from 0x{address:02X}: {e}")

        # Read event log (optional, use chunked read)
        event_log = None
        try:
            # Try reading all 96 bytes at once
            event_log_raw = self.bus.read_i2c_block_data(address, reg.REG_EVENT_LOG, 96)
            event_log = reg.parse_full_event_log(event_log_raw)
        except Exception:
            # Fall back to chunked read (32 bytes each)
            try:
                chunk1 = self.bus.read_i2c_block_data(address, reg.REG_EVENT_LOG, 32)
                chunk2 = self.bus.read_i2c_block_data(address, reg.REG_EVENT_LOG + 32, 32)
                chunk3 = self.bus.read_i2c_block_data(address, reg.REG_EVENT_LOG + 64, 32)
                event_log_raw = chunk1 + chunk2 + chunk3
                event_log = reg.parse_full_event_log(bytes(event_log_raw))
            except Exception as e:
                logger.debug(f"Failed to read event log from 0x{address:02X}: {e}")

        # Read EEPROM buffer if present (first 64 bytes for now)
        eeprom_data = None
        if status_flags['eeprom_present'] and not status_flags['eeprom_busy'] and eeprom_len > 0:
            try:
                eeprom_data = self.bus.read_i2c_block_data(address, reg.REG_EEPROM_BUF, min(64, eeprom_len))
            except Exception as e:
                logger.warning(f"Failed to read EEPROM from 0x{address:02X}: {e}")

        return {
            "status_flags": status,
            "temp_valid": status_flags['temp_valid'],
            "eeprom_present": status_flags['eeprom_present'],
            "eeprom_busy": status_flags['eeprom_busy'],
            "dock_changed": status_flags['dock_changed'],
            "temperature_c": temperature_c,
            "temperature_history": temp_history,
            "event_log": event_log,
            "eeprom_length": eeprom_len,
            "firmware_version": fw_version,
            "error_count": error_count,
            "uptime_ms": uptime_ms,
            "eeprom_data": eeprom_data,
            "timestamp": datetime.now()
        }

    def get_station_data(self, station_id: int) -> Optional[Dict]:
        """Get latest data for a station"""
        return self.station_data.get(station_id)

    async def get_status(self) -> Dict:
        """Get poller status"""
        return {
            "running": self.running,
            "last_poll": self.last_poll.isoformat() if self.last_poll else None,
            "stations_online": len([k for k, v in self.station_data.items() if v]),
            "error_counts": self.error_counts
        }


# Singleton instance
_poller = I2CPoller()


async def start_polling():
    """Start the I2C poller"""
    await _poller.start_polling()


def get_station_data(station_id: int) -> Optional[Dict]:
    """Get latest data for a station"""
    return _poller.get_station_data(station_id)


async def get_status() -> Dict:
    """Get poller status"""
    return await _poller.get_status()


async def get_system_status() -> Dict:
    """Get overall system status"""
    status = await _poller.get_status()
    return {
        "i2c_poller": status,
        "stations": _poller.station_data
    }
