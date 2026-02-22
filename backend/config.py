"""
Battery Test Bench - System Configuration
Version: 1.2.2

Changelog:
v1.2.2 (2026-02-18): Windows-safe SQLITE_DB_PATH default (relative to backend dir)
v1.2.1 (2026-02-16): Service shop model — updated I2C base 0x20, Siglent IPs,
                      safety limits for NiCd/aerospace, added test procedure defaults
v1.1.1 (2026-02-12): Updated for I2C register map fix (EVENT_LOG 0x200→0x30)
v1.0.0 (2026-02-12): Initial configuration module
"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    """System-wide configuration"""

    # Application
    APP_NAME: str = "Battery Test Bench"
    APP_VERSION: str = "1.2.1"
    DEBUG: bool = False

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1  # Single worker for shared I2C access

    # I2C Configuration
    I2C_BUS: int = 1  # /dev/i2c-1 on RPi5
    I2C_BASE_ADDRESS: int = 0x20  # First XIAO module (0x20-0x2B)
    I2C_STATION_COUNT: int = 12
    I2C_POLL_INTERVAL: float = 3.0  # seconds (faster for safety)
    I2C_TIMEOUT: float = 0.5  # seconds per transaction

    # InfluxDB Configuration
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""  # Set via environment variable
    INFLUXDB_ORG: str = "battery-bench"
    INFLUXDB_BUCKET: str = "station-data"
    INFLUXDB_RETENTION_DAYS: int = 365

    # SQLite Configuration
    SQLITE_DB_PATH: str = str(Path(__file__).parent / "data" / "battery_bench.db")

    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: float = 30.0  # seconds
    WS_MAX_CONNECTIONS: int = 10

    # Data Logging
    LOG_INTERVAL: float = 1.0  # seconds (1-second sampling during tests)
    LOG_IDLE_INTERVAL: float = 5.0  # seconds (slower when idle)
    LOG_QUEUE_SIZE: int = 5000

    # Safety Limits (global emergency defaults)
    EMERGENCY_TEMP_MAX_C: float = 60.0
    EMERGENCY_TEMP_MIN_C: float = -20.0
    TEMPERATURE_LOSS_TIMEOUT: float = 15.0  # seconds before abort
    MAX_VOLTAGE_MV: int = 10000  # 10V absolute maximum (NiCd safe range)
    MAX_CURRENT_MA: int = 10000  # 10A absolute maximum

    # SCPI Equipment — Siglent SPD1168X (PSU) and SDL1030X (Load)
    SCPI_TIMEOUT: float = 2.0  # seconds
    SCPI_RETRY_COUNT: int = 3
    PSU_IP_BASE: str = "192.168.1.101"  # PSU IPs: .101-.112
    LOAD_IP_BASE: str = "192.168.1.201"  # Load IPs: .201-.212
    SCPI_PORT: int = 5025

    # Authentication
    AUTHENTIK_URL: str = ""  # Set via environment variable
    AUTHENTIK_CLIENT_ID: str = ""
    AUTHENTIK_CLIENT_SECRET: str = ""
    JWT_SECRET_KEY: str = ""  # Generate with: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # File Paths
    DATA_DIR: str = "/opt/battery-bench/data"
    REPORTS_DIR: str = "/opt/battery-bench/reports"
    LOGS_DIR: str = "/opt/battery-bench/logs"

    # EEPROM Configuration
    EEPROM_SIZE: int = 512  # DS24B33 size in bytes
    EEPROM_WRITE_TIMEOUT: float = 10.0  # seconds
    EEPROM_UNLOCK_KEY: int = 0xA55A

    # Station State Machine
    STATE_TRANSITION_DELAY: float = 1.0  # seconds
    DOCK_DEBOUNCE_TIME: float = 2.0  # seconds

    # Test Procedure Defaults (overridden by battery_profiles table)
    DEFAULT_CHARGE_TEMP_MAX_C: float = 45.0
    DEFAULT_DISCHARGE_TEMP_MAX_C: float = 45.0
    REST_PERIOD_AGE_THRESHOLD_MONTHS: int = 24
    REST_PERIOD_DURATION_H: int = 24

    # Report Generation
    REPORT_DPI: int = 300
    REPORT_PLOT_WIDTH: int = 10  # inches
    REPORT_PLOT_HEIGHT: int = 6  # inches

    # Calibration Tracking
    CALIBRATION_WARNING_DAYS: int = 30  # Days before expiry warning
    CALIBRATION_INTERVAL_DAYS: int = 365  # Annual calibration

    # Work Order Numbering
    WORK_ORDER_PREFIX: str = "WO"
    WORK_ORDER_YEAR_FORMAT: bool = True  # WO-2026-00001

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()


# Station-specific configuration
def get_xiao_address(station_id: int) -> int:
    """Get I2C address for a station (1-12) → 0x20-0x2B"""
    if not 1 <= station_id <= settings.I2C_STATION_COUNT:
        raise ValueError(f"Invalid station ID: {station_id}")
    return settings.I2C_BASE_ADDRESS + (station_id - 1)


def get_psu_ip(station_id: int) -> str:
    """Get Siglent SPD1168X PSU IP for a station (1-12) → .101-.112"""
    if not 1 <= station_id <= settings.I2C_STATION_COUNT:
        raise ValueError(f"Invalid station ID: {station_id}")
    base_parts = settings.PSU_IP_BASE.rsplit('.', 1)
    base_ip = int(base_parts[1])
    return f"{base_parts[0]}.{base_ip + station_id - 1}"


def get_load_ip(station_id: int) -> str:
    """Get Siglent SDL1030X Load IP for a station (1-12) → .201-.212"""
    if not 1 <= station_id <= settings.I2C_STATION_COUNT:
        raise ValueError(f"Invalid station ID: {station_id}")
    base_parts = settings.LOAD_IP_BASE.rsplit('.', 1)
    base_ip = int(base_parts[1])
    return f"{base_parts[0]}.{base_ip + station_id - 1}"


# Create required directories
def init_directories():
    """Create necessary directories if they don't exist"""
    for directory in [settings.DATA_DIR, settings.REPORTS_DIR, settings.LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    print(f"Battery Test Bench Configuration v{settings.APP_VERSION}")
    print(f"I2C Bus: {settings.I2C_BUS}")
    print(f"Station Count: {settings.I2C_STATION_COUNT}")
    print(f"XIAO Addresses: 0x{settings.I2C_BASE_ADDRESS:02X} - "
          f"0x{settings.I2C_BASE_ADDRESS + settings.I2C_STATION_COUNT - 1:02X}")
    print(f"InfluxDB: {settings.INFLUXDB_URL}")
    print(f"SQLite: {settings.SQLITE_DB_PATH}")
    print(f"\nStation IP Assignments (Siglent Equipment):")
    for i in range(1, 13):
        print(f"  Station {i:2d}: XIAO 0x{get_xiao_address(i):02X}  "
              f"PSU {get_psu_ip(i)}  Load {get_load_ip(i)}")
