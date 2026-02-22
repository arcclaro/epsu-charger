"""
Battery Test Bench - XIAO RP2040 I2C Register Map
Version: 1.2.1

Changelog:
v1.2.1 (2026-02-16): Corrected base address 0x10→0x20; clarified RP2040 scope
                      (temperature + EEPROM only — no voltage/current measurement)
v1.1.1 (2026-02-12): Fixed EVENT_LOG register address (0x200 → 0x30)
v1.0.0 (2026-02-12): Initial register definitions

NOTE ON SCOPE:
  The XIAO RP2040 modules ONLY handle 1-Wire devices:
    - MAX31820 temperature sensor(s)
    - DS24B33 EEPROM
  Voltage and current measurements come from Siglent SCPI equipment
  (SPD1168X PSU and SDL1030X Load) via Ethernet, NOT from the RP2040.
"""

# =============================================================================
# XIAO RP2040 I2C Register Map - Firmware v1.1+
# =============================================================================
#
# RP2040 reads: Temperature (1-Wire MAX31820) + EEPROM (1-Wire DS24B33)
# RP2040 does NOT read: Voltage, Current (those come from SCPI equipment)
#
# I2C addresses: 0x20-0x2B (stations 1-12)
# All registers within 8-bit address space (0x00-0xFF)
#

# =============================================================================
# Core Status Registers (0x00-0x1F)
# =============================================================================

REG_STATUS = 0x00              # Status flags (1 byte)
REG_STATION_ID = 0x01          # Station ID 1-12 (1 byte)
REG_TEMP_RAW = 0x02            # Primary temperature (2 bytes, signed, 0.0625°C/LSB)
REG_EEPROM_LEN = 0x04          # EEPROM length (2 bytes, little-endian)
REG_FW_VERSION = 0x06          # Firmware version (1 byte, format: major<<4 | minor)
REG_ERROR_COUNT = 0x07         # I2C/1-Wire error counter (1 byte)

# Extended diagnostics (0x08-0x1F)
REG_EEPROM_CRC16 = 0x08        # EEPROM CRC-16 (2 bytes, little-endian)
REG_UPTIME = 0x0A              # System uptime (4 bytes, milliseconds)
REG_LAST_TEMP_TIME = 0x0E      # Last temp reading timestamp (4 bytes, ms)
REG_DOCK_CHANGE_TIME = 0x12    # Last dock change timestamp (4 bytes, ms)
REG_TEMP_AGE = 0x16            # Temperature age (2 bytes, milliseconds since last read)
REG_TEMP_DELTA_FLAGS = 0x18    # Temperature delta flags (1 byte)
REG_TEMP_DELTA = 0x19          # Temperature delta since last read (1 byte, signed, 0.0625°C/LSB)
REG_TEMP_RAW2 = 0x1A           # Secondary temperature sensor (2 bytes, optional dual-sensor mode)
REG_OW_RESET_FAILS = 0x1C      # 1-Wire reset failure count (1 byte)
REG_OW_CRC_ERRORS = 0x1D       # 1-Wire CRC error count (1 byte)
REG_OW_TIMEOUTS = 0x1E         # 1-Wire timeout count (1 byte)
REG_EEPROM_WRITE_COUNT = 0x1F  # EEPROM write count LSB (1 byte)

# =============================================================================
# Buffer Registers (0x20-0xEF)
# =============================================================================

REG_TEMP_HISTORY = 0x20        # Temperature history buffer (16 bytes)
                               # 8 most recent readings × 2 bytes each
                               # Format: same as REG_TEMP_RAW

REG_EVENT_LOG = 0x30           # Event log buffer (96 bytes)
                               # ⚠️ UPDATED: Was 0x200, now 0x30 for 8-bit addressing
                               # 16 events × 6 bytes per event
                               # Event format:
                               #   [0-3]: timestamp (uint32, ms)
                               #   [4]:   event type (uint8)
                               #   [5]:   event data (uint8)

# Reserved for future use (0x90-0xEF)

# =============================================================================
# EEPROM Buffer (0x10-0x0F + 512 bytes, overlaps with above)
# =============================================================================

REG_EEPROM_BUF = 0x10          # EEPROM buffer start
                               # Note: This overlaps with other registers
                               # Read EEPROM data separately from status reads
                               # Length: Variable, up to 512 bytes
                               # Actual length stored in REG_EEPROM_LEN

# =============================================================================
# Command Register (0xFF)
# =============================================================================

REG_COMMAND = 0xFF             # Command register (write-only)

# Command codes:
CMD_FORCE_RESCAN = 0x01        # Force 1-Wire bus rescan
CMD_RELOAD_EEPROM = 0x02       # Reload EEPROM from DS24B33
CMD_WRITE_EEPROM = 0x03        # Write EEPROM buffer to DS24B33 (requires unlock)
CMD_UNLOCK_WRITE = 0x04        # Unlock EEPROM write mode (key: 0xA55A at 0x08)
CMD_RESET_ERRORS = 0x05        # Reset error counters
CMD_SELF_TEST = 0xFE           # Run self-test sequence

# =============================================================================
# Status Flags (REG_STATUS, 0x00)
# =============================================================================

STATUS_TEMP_VALID = 0x01       # Bit 0: Temperature reading valid
STATUS_EEPROM_PRESENT = 0x02   # Bit 1: EEPROM detected on 1-Wire
STATUS_EEPROM_BUSY = 0x04      # Bit 2: EEPROM read/write in progress
STATUS_WRITE_OK = 0x08         # Bit 3: Last EEPROM write successful
STATUS_WRITE_ERROR = 0x10      # Bit 4: Last EEPROM write failed
STATUS_DOCK_CHANGED = 0x20     # Bit 5: Battery dock inserted/removed (cleared on read)
# Bits 6-7: Reserved

# =============================================================================
# Event Log Event Types (byte 4 of each event)
# =============================================================================

EVENT_BOOT = 0x00              # System boot/reset
EVENT_DOCK_INSERTED = 0x01     # Battery dock detected
EVENT_DOCK_REMOVED = 0x02      # Battery dock removed
EVENT_TEMP_VALID = 0x03        # Temperature sensor became valid
EVENT_TEMP_LOST = 0x04         # Temperature sensor lost
EVENT_EEPROM_READ_OK = 0x05    # EEPROM read successful
EVENT_EEPROM_READ_FAIL = 0x06  # EEPROM read failed
EVENT_EEPROM_WRITE_OK = 0x07   # EEPROM write successful
EVENT_EEPROM_WRITE_FAIL = 0x08 # EEPROM write failed
EVENT_OW_RESET_FAIL = 0x09     # 1-Wire reset failure
EVENT_OW_CRC_ERROR = 0x0A      # 1-Wire CRC error
EVENT_I2C_ERROR = 0x0B         # I2C communication error
EVENT_TEMP_CHANGE = 0x0C       # Significant temperature change
EVENT_UNLOCK_MODE = 0x0D       # Write unlock mode activated
EVENT_COMMAND_RX = 0x0E        # Command received
# 0x0F-0xFF: Reserved

# =============================================================================
# Helper Constants
# =============================================================================

# Temperature conversion
TEMP_LSB_TO_CELSIUS = 0.0625   # Each LSB = 0.0625°C

# I2C addressing
I2C_BASE_ADDRESS = 0x20        # Station 1 address (0x20-0x2B)
I2C_MAX_STATIONS = 12          # 12 stations

# EEPROM
EEPROM_MAX_SIZE = 512          # DS24B33 size
EEPROM_UNLOCK_KEY = 0xA55A     # Write unlock key

# Timeouts
EEPROM_BUSY_TIMEOUT_MS = 5000  # Max wait for EEPROM operation
UNLOCK_TIMEOUT_MS = 10000      # Write unlock expires after 10s

# =============================================================================
# Helper Functions
# =============================================================================

def get_station_address(station_id: int) -> int:
    """
    Get I2C address for a station (1-12)

    Args:
        station_id: Station number (1-12)

    Returns:
        I2C address (0x20-0x2B)

    Raises:
        ValueError: If station_id out of range
    """
    if not 1 <= station_id <= I2C_MAX_STATIONS:
        raise ValueError(f"Invalid station ID: {station_id} (must be 1-{I2C_MAX_STATIONS})")
    return I2C_BASE_ADDRESS + (station_id - 1)


def parse_temperature(raw_value: int) -> float:
    """
    Convert raw temperature value to Celsius

    Args:
        raw_value: 16-bit signed temperature value from sensor

    Returns:
        Temperature in degrees Celsius
    """
    # Handle negative values (two's complement)
    if raw_value & 0x8000:
        raw_value -= 0x10000
    return raw_value * TEMP_LSB_TO_CELSIUS


def parse_status_flags(status: int) -> dict:
    """
    Parse status byte into flag dictionary

    Args:
        status: Status byte from REG_STATUS

    Returns:
        Dictionary with boolean flags
    """
    return {
        'temp_valid': bool(status & STATUS_TEMP_VALID),
        'eeprom_present': bool(status & STATUS_EEPROM_PRESENT),
        'eeprom_busy': bool(status & STATUS_EEPROM_BUSY),
        'write_ok': bool(status & STATUS_WRITE_OK),
        'write_error': bool(status & STATUS_WRITE_ERROR),
        'dock_changed': bool(status & STATUS_DOCK_CHANGED),
    }


def parse_event_log_entry(event_data: bytes) -> dict:
    """
    Parse a single 6-byte event log entry

    Args:
        event_data: 6 bytes from event log

    Returns:
        Dictionary with event details
    """
    if len(event_data) != 6:
        raise ValueError("Event data must be exactly 6 bytes")

    timestamp = int.from_bytes(event_data[0:4], 'little')
    event_type = event_data[4]
    event_data_byte = event_data[5]

    # Map event types to names
    event_names = {
        EVENT_BOOT: "Boot",
        EVENT_DOCK_INSERTED: "Dock Inserted",
        EVENT_DOCK_REMOVED: "Dock Removed",
        EVENT_TEMP_VALID: "Temperature Valid",
        EVENT_TEMP_LOST: "Temperature Lost",
        EVENT_EEPROM_READ_OK: "EEPROM Read OK",
        EVENT_EEPROM_READ_FAIL: "EEPROM Read Failed",
        EVENT_EEPROM_WRITE_OK: "EEPROM Write OK",
        EVENT_EEPROM_WRITE_FAIL: "EEPROM Write Failed",
        EVENT_OW_RESET_FAIL: "1-Wire Reset Fail",
        EVENT_OW_CRC_ERROR: "1-Wire CRC Error",
        EVENT_I2C_ERROR: "I2C Error",
        EVENT_TEMP_CHANGE: "Temperature Change",
        EVENT_UNLOCK_MODE: "Write Unlock",
        EVENT_COMMAND_RX: "Command Received",
    }

    return {
        'timestamp_ms': timestamp,
        'event_type': event_type,
        'event_name': event_names.get(event_type, f"Unknown (0x{event_type:02X})"),
        'event_data': event_data_byte,
    }


def parse_full_event_log(log_data: bytes) -> list:
    """
    Parse complete 96-byte event log

    Args:
        log_data: 96 bytes from REG_EVENT_LOG

    Returns:
        List of event dictionaries (up to 16 events)
    """
    if len(log_data) != 96:
        raise ValueError("Event log must be exactly 96 bytes")

    events = []
    for i in range(16):
        offset = i * 6
        event_bytes = log_data[offset:offset + 6]

        # Skip empty events (timestamp == 0)
        timestamp = int.from_bytes(event_bytes[0:4], 'little')
        if timestamp == 0:
            continue

        events.append(parse_event_log_entry(event_bytes))

    return events


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    print("XIAO RP2040 Register Map - Battery Test Bench")
    print("=" * 60)
    print(f"Core Registers:      0x{REG_STATUS:02X} - 0x{REG_EEPROM_WRITE_COUNT:02X}")
    print(f"Temperature History: 0x{REG_TEMP_HISTORY:02X} (16 bytes)")
    print(f"Event Log:           0x{REG_EVENT_LOG:02X} (96 bytes) ⚠️ UPDATED")
    print(f"EEPROM Buffer:       0x{REG_EEPROM_BUF:02X} (up to 512 bytes)")
    print(f"Command Register:    0x{REG_COMMAND:02X}")
    print()
    print("Station I2C Addresses:")
    for station_id in range(1, 13):
        addr = get_station_address(station_id)
        print(f"  Station {station_id:2d}: 0x{addr:02X}")
    print()
    print("Temperature Conversion:")
    print(f"  Raw value 408 (0x198) = {parse_temperature(408):.2f}°C")
    print(f"  Raw value -80 (0xFF50) = {parse_temperature(0xFF50):.2f}°C")
