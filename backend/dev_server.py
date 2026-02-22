"""
Battery Test Bench - Development Server with Mock Hardware
Version: 1.0.2

Changelog:
v1.0.2 (2026-02-12): Windows testing support with mocked I2C/SCPI
"""

import os
import sys

# Enable mock mode BEFORE importing anything else
os.environ['MOCK_I2C'] = 'true'
os.environ['MOCK_SCPI'] = 'true'
os.environ['DEBUG'] = 'true'

# Mock smbus2 if not available (Windows)
try:
    import smbus2
    print("INFO: smbus2 already installed")
except ImportError:
    print("WARNING: smbus2 not available, creating mock")
    sys.modules['smbus2'] = type(sys)('smbus2')

    class MockSMBus:
        """Mock SMBus for Windows testing"""

        def __init__(self, bus):
            self.bus = bus
            print(f"✓ Mock I2C bus {bus} initialized")

        def read_byte_data(self, addr, reg):
            """Mock single byte read"""
            # Mock status register
            if reg == 0x00:
                # TEMP_VALID | EEPROM_PRESENT
                return 0x03
            # Mock station ID
            if reg == 0x01:
                return (addr - 0x10 + 1)
            # Mock firmware version (v1.0)
            if reg == 0x06:
                return 0x10
            return 0

        def read_word_data(self, addr, reg):
            """Mock 16-bit read"""
            import random

            # Mock temperature (20-30°C)
            if reg == 0x02:
                temp_c = 20 + random.uniform(0, 10)
                temp_raw = int(temp_c * 16)
                return temp_raw

            # Mock EEPROM length
            if reg == 0x04:
                return 512

            return 0

        def read_i2c_block_data(self, addr, reg, length):
            """Mock block read (for EEPROM)"""
            # Mock EEPROM data
            if reg >= 0x10:
                data = []
                # Format version
                data.append(1)
                # Battery type (Li-ion)
                data.append(3)
                # Capacity (2000 mAh) - little endian
                data.extend([0xD0, 0x07])
                # Max voltage (4200 mV)
                data.extend([0x68, 0x10])
                # Max discharge current (2000 mA)
                data.extend([0xD0, 0x07])
                # Max charge current (1000 mA)
                data.extend([0xE8, 0x03])
                # Min voltage (3000 mV)
                data.extend([0xB8, 0x0B])
                # Max temp (45.0°C = 450)
                data.extend([0xC2, 0x01])
                # Min temp (-10.0°C = -100)
                data.extend([0x9C, 0xFF])

                # Pad to requested length
                while len(data) < length:
                    data.append(0)

                return data[:length]

            return [0] * length

        def write_byte_data(self, addr, reg, value):
            """Mock single byte write"""
            station = addr - 0x10 + 1
            print(f"  Mock I2C write: Station {station}, reg=0x{reg:02X}, value=0x{value:02X}")

        def write_word_data(self, addr, reg, value):
            """Mock 16-bit write"""
            station = addr - 0x10 + 1
            print(f"  Mock I2C write: Station {station}, reg=0x{reg:02X}, value=0x{value:04X}")

        def write_i2c_block_data(self, addr, reg, data):
            """Mock block write"""
            station = addr - 0x10 + 1
            print(f"  Mock I2C write: Station {station}, reg=0x{reg:02X}, {len(data)} bytes")

        def close(self):
            """Close bus"""
            pass

    sys.modules['smbus2'].SMBus = MockSMBus

print("=" * 60)
print("    Battery Test Bench - Development Server")
print("=" * 60)
print()
print("MOCK MODE ENABLED FOR WINDOWS TESTING:")
print("  ✓ I2C hardware mocked (12 virtual stations)")
print("  ✓ SCPI devices mocked (PSUs and Loads)")
print("  ✓ Temperature sensors mocked (20-30°C)")
print("  ✓ EEPROM data mocked (Li-ion battery config)")
print()
print("AVAILABLE FEATURES:")
print("  ✓ REST API (all endpoints)")
print("  ✓ WebSocket real-time updates")
print("  ✓ SQLite database")
print("  ✓ Recipe management")
print("  ✓ Session history")
print("  ✓ Admin panel")
print()
print("LIMITATIONS:")
print("  ✗ No real I2C communication")
print("  ✗ No actual battery testing")
print("  ✗ PSU/Load control is simulated")
print()
print("Starting FastAPI server...")
print("  Backend API: http://localhost:8000")
print("  API Docs:    http://localhost:8000/docs")
print("  Health:      http://localhost:8000/api/health")
print()
print("Press Ctrl+C to stop")
print("=" * 60)
print()

# Now import and run the app
from main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
