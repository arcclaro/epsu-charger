"""
Battery Test Bench - EEPROM Manager Service
Version: 1.2.7

Changelog:
v1.2.7 (2026-02-16): Comprehensive EEPROM layout v2 for BatteryConfig v1.2.6;
                      supports all CMM-derived fields (DIEHL 3301-31, Cobham 301-3017,
                      DIEHL 3214-31); 160-byte data block + 32+32+8 strings + CRC
v1.2.2 (2026-02-16): Updated for battery MODEL parameters (not per-unit);
                      EEPROM holds model-specific charge/discharge/safety config
v1.0.1 (2026-02-12): Initial EEPROM manager

The DS24B33 EEPROM on each battery dock stores the battery MODEL parameters:
- Chemistry type, capacity, cell count, nominal voltage
- Standard charge: current, voltage limit, duration
- Reconditioning charge: current, duration, storage threshold
- Trickle charge current
- Capacity test: discharge current, end voltage, max duration, rest before
- Capacity pass/fail: min minutes, min capacity %, voltage check time/voltage
- Fast discharge: enabled, current, end voltage, pass min time, rest before
- Pre-discharge: current, end voltage
- Post-charge: enabled, duration
- Temperature limits: charge max, discharge max, emergency max, operating min
- Safety: absolute min voltage
- Age rest: threshold months, duration
- Model identification: part number, model description, manufacturer code

This tells the main system exactly how to handle this battery model.
Per-unit data (serial number, test history, cycles) is tracked in the database.
"""

import logging
from typing import Optional
from models.station import BatteryConfig, BatteryType
from services import i2c_poller

logger = logging.getLogger(__name__)

# =============================================================================
# EEPROM Layout v2 (DS24B33 via RP2040 I2C buffer at REG_EEPROM_BUF)
# Total: 512 bytes (4Kb DS24B33), using 152 bytes (0x98)
# =============================================================================
#
# --- Header (0x00-0x03) ---
# Offset  Size  Field
# 0x00    1     Format version (2 = CMM-compliant v2)
# 0x01    1     Battery type (0=NiCd, 1=NiMH, 2=LiFePO4, 3=Li-Ion, 4=SLA)
# 0x02    2     Nominal capacity (mAh, u16 LE)
#
# --- Cell info (0x04-0x07) ---
# 0x04    1     Cell count
# 0x05    1     Reserved
# 0x06    2     Nominal voltage (mV, u16 LE)
#
# --- Standard charge (0x08-0x0F) ---
# 0x08    2     Charge voltage limit (mV, u16 LE)
# 0x0A    2     Standard charge current (mA, u16 LE)
# 0x0C    2     Standard charge duration (minutes, u16 LE)
# 0x0E    2     Trickle charge current (mA, u16 LE)
#
# --- Reconditioning charge (0x10-0x17) ---
# 0x10    2     Recondition charge current (mA, u16 LE)
# 0x12    2     Recondition charge duration (minutes, u16 LE)
# 0x14    2     Recondition storage threshold (months, u16 LE)
# 0x16    2     Reserved
#
# --- Capacity test discharge (0x18-0x21) ---
# 0x18    2     Cap test discharge current (mA, u16 LE)
# 0x1A    2     Cap test end voltage (mV, u16 LE)
# 0x1C    2     Cap test max duration (minutes, u16 LE)
# 0x1E    2     Cap test rest before (minutes, u16 LE)
#
# --- Capacity pass/fail criteria (0x20-0x27) ---
# 0x20    2     Cap test pass min minutes (u16 LE, 0=not used)
# 0x22    2     Cap test pass min capacity % (u16 LE, 0=not used)
# 0x24    2     Cap test voltage check time (minutes, u16 LE, 0=not used)
# 0x26    2     Cap test voltage check min (mV, u16 LE, 0=not used)
#
# --- Fast discharge (0x28-0x33) ---
# 0x28    1     Fast discharge enabled (0/1)
# 0x29    1     Reserved
# 0x2A    2     Fast discharge current (mA, u16 LE)
# 0x2C    2     Fast discharge end voltage (mV, u16 LE)
# 0x2E    2     Fast discharge pass min minutes (u16 LE)
# 0x30    2     Fast discharge rest before (minutes, u16 LE)
# 0x32    2     Reserved
#
# --- Pre-discharge (0x34-0x37) ---
# 0x34    2     Pre-discharge current (mA, u16 LE, 0=use cap_test current)
# 0x36    2     Pre-discharge end voltage (mV, u16 LE, 0=use cap_test value)
#
# --- Post-charge (0x38-0x3B) ---
# 0x38    1     Post-charge enabled (0/1)
# 0x39    1     Reserved
# 0x3A    2     Post-charge duration (minutes, u16 LE)
#
# --- Temperature limits (0x3C-0x43) ---
# 0x3C    2     Max charge temp (deg C x 10, s16 LE)
# 0x3E    2     Max discharge temp (deg C x 10, s16 LE)
# 0x40    2     Emergency temp max (deg C x 10, s16 LE)
# 0x42    2     Min operating temp (deg C x 10, s16 LE)
#
# --- Safety (0x44-0x47) ---
# 0x44    2     Absolute min voltage (mV, u16 LE)
# 0x46    2     Reserved
#
# --- Age rest (0x48-0x4B) ---
# 0x48    2     Age rest threshold (months, u16 LE)
# 0x4A    2     Age rest duration (minutes, u16 LE)
#
# --- CRC (0x4C-0x4D) ---
# 0x4C    2     CRC-16 of bytes 0x00-0x4B (u16 LE)
# 0x4E    2     Reserved
#
# --- Strings (0x50-0xA7) ---
# 0x50    32    Part number (null-terminated ASCII)
# 0x70    32    Model description (null-terminated ASCII)
# 0x90    8     Manufacturer code (null-terminated ASCII)
# 0x98    ...   Reserved / future use
#

# Layout constants
_HEADER_SIZE = 0x4E  # Data block before strings (includes CRC + reserved)
_CRC_OFFSET = 0x4C
_CRC_DATA_END = 0x4C  # CRC covers 0x00..0x4B
_PART_NUMBER_OFFSET = 0x50
_MODEL_DESC_OFFSET = 0x70
_MFG_CODE_OFFSET = 0x90
_MIN_EEPROM_SIZE = 0x98  # 152 bytes minimum for all fields


async def read_battery_config(station_id: int) -> Optional[BatteryConfig]:
    """
    Read battery MODEL configuration from EEPROM via I2C.
    EEPROM data is cached in XIAO RP2040's I2C register buffer.

    Returns BatteryConfig with all model-level test parameters,
    or None if EEPROM is not present/readable.
    """
    i2c_data = i2c_poller.get_station_data(station_id)

    if not i2c_data or not i2c_data.get("eeprom_present"):
        return None

    eeprom_data = i2c_data.get("eeprom_data")
    if not eeprom_data or len(eeprom_data) < _MIN_EEPROM_SIZE:
        logger.error(f"Station {station_id}: Insufficient EEPROM data "
                     f"(got {len(eeprom_data) if eeprom_data else 0} bytes, "
                     f"need {_MIN_EEPROM_SIZE})")
        return None

    try:
        # Verify format version
        format_version = eeprom_data[0x00]
        if format_version != 2:
            logger.warning(f"Station {station_id}: Unknown EEPROM format "
                           f"version {format_version} (expected 2)")

        # CRC check
        stored_crc = _read_u16(eeprom_data, _CRC_OFFSET)
        computed_crc = _crc16(eeprom_data[0x00:_CRC_DATA_END])
        if stored_crc != computed_crc:
            logger.warning(f"Station {station_id}: EEPROM CRC mismatch "
                          f"(stored=0x{stored_crc:04X}, "
                          f"computed=0x{computed_crc:04X})")

        # --- Header ---
        battery_type = BatteryType(eeprom_data[0x01])
        nominal_capacity_mah = _read_u16(eeprom_data, 0x02)

        # --- Cell info ---
        cell_count = eeprom_data[0x04]
        nominal_voltage_mv = _read_u16(eeprom_data, 0x06)

        # --- Standard charge ---
        charge_voltage_limit_mv = _read_u16(eeprom_data, 0x08)
        standard_charge_current_ma = _read_u16(eeprom_data, 0x0A)
        standard_charge_duration_min = _read_u16(eeprom_data, 0x0C)
        trickle_charge_current_ma = _read_u16(eeprom_data, 0x0E)

        # --- Reconditioning charge ---
        recondition_charge_current_ma = _read_u16(eeprom_data, 0x10)
        recondition_charge_duration_min = _read_u16(eeprom_data, 0x12)
        recondition_storage_threshold_months = _read_u16(eeprom_data, 0x14)

        # --- Capacity test discharge ---
        cap_test_discharge_current_ma = _read_u16(eeprom_data, 0x18)
        cap_test_end_voltage_mv = _read_u16(eeprom_data, 0x1A)
        cap_test_max_duration_min = _read_u16(eeprom_data, 0x1C)
        cap_test_rest_before_min = _read_u16(eeprom_data, 0x1E)

        # --- Capacity pass/fail criteria ---
        cap_test_pass_min_minutes = _read_u16(eeprom_data, 0x20)
        cap_test_pass_min_capacity_pct = _read_u16(eeprom_data, 0x22)
        cap_test_voltage_check_time_min = _read_u16(eeprom_data, 0x24)
        cap_test_voltage_check_min_mv = _read_u16(eeprom_data, 0x26)

        # --- Fast discharge ---
        fast_discharge_enabled = bool(eeprom_data[0x28])
        fast_discharge_current_ma = _read_u16(eeprom_data, 0x2A)
        fast_discharge_end_voltage_mv = _read_u16(eeprom_data, 0x2C)
        fast_discharge_pass_min_minutes = _read_u16(eeprom_data, 0x2E)
        fast_discharge_rest_before_min = _read_u16(eeprom_data, 0x30)

        # --- Pre-discharge ---
        pre_discharge_current_ma = _read_u16(eeprom_data, 0x34)
        pre_discharge_end_voltage_mv = _read_u16(eeprom_data, 0x36)

        # --- Post-charge ---
        post_charge_enabled = bool(eeprom_data[0x38])
        post_charge_duration_min = _read_u16(eeprom_data, 0x3A)

        # --- Temperature limits (stored as deg C x 10, signed) ---
        max_charge_temp_c = _read_s16(eeprom_data, 0x3C) / 10.0
        max_discharge_temp_c = _read_s16(eeprom_data, 0x3E) / 10.0
        emergency_temp_max_c = _read_s16(eeprom_data, 0x40) / 10.0
        min_operating_temp_c = _read_s16(eeprom_data, 0x42) / 10.0

        # --- Safety ---
        absolute_min_voltage_mv = _read_u16(eeprom_data, 0x44)

        # --- Age rest ---
        age_rest_threshold_months = _read_u16(eeprom_data, 0x48)
        age_rest_duration_min = _read_u16(eeprom_data, 0x4A)

        # --- Strings ---
        part_number = _parse_string(eeprom_data[_PART_NUMBER_OFFSET:_PART_NUMBER_OFFSET + 32])
        model_description = _parse_string(eeprom_data[_MODEL_DESC_OFFSET:_MODEL_DESC_OFFSET + 32])
        manufacturer_code = _parse_string(eeprom_data[_MFG_CODE_OFFSET:_MFG_CODE_OFFSET + 8])

        return BatteryConfig(
            format_version=format_version,
            battery_type=battery_type,
            nominal_capacity_mah=nominal_capacity_mah,
            cell_count=cell_count,
            nominal_voltage_mv=nominal_voltage_mv,
            charge_voltage_limit_mv=charge_voltage_limit_mv,
            standard_charge_current_ma=standard_charge_current_ma,
            standard_charge_duration_min=standard_charge_duration_min,
            trickle_charge_current_ma=trickle_charge_current_ma,
            recondition_charge_current_ma=recondition_charge_current_ma,
            recondition_charge_duration_min=recondition_charge_duration_min,
            recondition_storage_threshold_months=recondition_storage_threshold_months,
            cap_test_discharge_current_ma=cap_test_discharge_current_ma,
            cap_test_end_voltage_mv=cap_test_end_voltage_mv,
            cap_test_max_duration_min=cap_test_max_duration_min,
            cap_test_rest_before_min=cap_test_rest_before_min,
            cap_test_pass_min_minutes=cap_test_pass_min_minutes,
            cap_test_pass_min_capacity_pct=cap_test_pass_min_capacity_pct,
            cap_test_voltage_check_time_min=cap_test_voltage_check_time_min,
            cap_test_voltage_check_min_mv=cap_test_voltage_check_min_mv,
            fast_discharge_enabled=fast_discharge_enabled,
            fast_discharge_current_ma=fast_discharge_current_ma,
            fast_discharge_end_voltage_mv=fast_discharge_end_voltage_mv,
            fast_discharge_pass_min_minutes=fast_discharge_pass_min_minutes,
            fast_discharge_rest_before_min=fast_discharge_rest_before_min,
            pre_discharge_current_ma=pre_discharge_current_ma,
            pre_discharge_end_voltage_mv=pre_discharge_end_voltage_mv,
            post_charge_enabled=post_charge_enabled,
            post_charge_duration_min=post_charge_duration_min,
            max_charge_temp_c=max_charge_temp_c,
            max_discharge_temp_c=max_discharge_temp_c,
            emergency_temp_max_c=emergency_temp_max_c,
            min_operating_temp_c=min_operating_temp_c,
            absolute_min_voltage_mv=absolute_min_voltage_mv,
            age_rest_threshold_months=age_rest_threshold_months,
            age_rest_duration_min=age_rest_duration_min,
            part_number=part_number,
            model_description=model_description,
            manufacturer_code=manufacturer_code,
        )

    except Exception as e:
        logger.error(f"Station {station_id}: Failed to parse EEPROM data: {e}")
        return None


def build_test_params_from_eeprom(config: BatteryConfig, battery_age_months: int = 0,
                                   months_since_last_service: int = 0):
    """
    Build TestParameters from EEPROM battery model config.

    Applies CMM-derived rules:
    - Age-based extended rest (e.g., 24h for batteries >= 24 months old)
    - Reconditioning charge if stored > threshold months
    - Pre-discharge current defaults to cap_test current if not specified
    - Post-charge for storage/delivery
    """
    from services.test_controller import TestParameters

    # Pre-discharge: use dedicated current or fall back to cap_test current
    pre_discharge_current_ma = (config.pre_discharge_current_ma
                                 if config.pre_discharge_current_ma > 0
                                 else config.cap_test_discharge_current_ma)
    pre_discharge_end_voltage_mv = (config.pre_discharge_end_voltage_mv
                                     if config.pre_discharge_end_voltage_mv > 0
                                     else config.cap_test_end_voltage_mv)

    # Age-based rest
    needs_age_rest = battery_age_months >= config.age_rest_threshold_months
    rest_before_min = config.cap_test_rest_before_min
    if needs_age_rest and config.age_rest_duration_min > rest_before_min:
        rest_before_min = config.age_rest_duration_min

    # Reconditioning: applies if stored longer than threshold
    needs_reconditioning = (config.recondition_charge_current_ma > 0 and
                            months_since_last_service >= config.recondition_storage_threshold_months)

    return TestParameters(
        # Standard charge
        charge_current_ma=config.standard_charge_current_ma,
        charge_voltage_limit_mv=config.charge_voltage_limit_mv,
        charge_duration_min=config.standard_charge_duration_min,
        charge_temp_max_c=config.max_charge_temp_c,

        # Reconditioning
        needs_reconditioning=needs_reconditioning,
        recondition_charge_current_ma=config.recondition_charge_current_ma,
        recondition_charge_duration_min=config.recondition_charge_duration_min,

        # Capacity test discharge
        cap_test_discharge_current_ma=config.cap_test_discharge_current_ma,
        cap_test_end_voltage_mv=config.cap_test_end_voltage_mv,
        cap_test_max_duration_min=config.cap_test_max_duration_min,
        discharge_temp_max_c=config.max_discharge_temp_c,

        # Pass/fail criteria
        cap_test_pass_min_minutes=config.cap_test_pass_min_minutes,
        cap_test_pass_min_capacity_pct=config.cap_test_pass_min_capacity_pct,
        nominal_capacity_mah=config.nominal_capacity_mah,
        cap_test_voltage_check_time_min=config.cap_test_voltage_check_time_min,
        cap_test_voltage_check_min_mv=config.cap_test_voltage_check_min_mv,

        # Fast discharge
        fast_discharge_enabled=config.fast_discharge_enabled,
        fast_discharge_current_ma=config.fast_discharge_current_ma,
        fast_discharge_end_voltage_mv=config.fast_discharge_end_voltage_mv,
        fast_discharge_pass_min_minutes=config.fast_discharge_pass_min_minutes,
        fast_discharge_rest_before_min=config.fast_discharge_rest_before_min,

        # Pre-discharge
        pre_discharge_current_ma=pre_discharge_current_ma,
        pre_discharge_end_voltage_mv=pre_discharge_end_voltage_mv,

        # Rest
        rest_before_discharge_min=rest_before_min,

        # Post-charge
        post_charge_enabled=config.post_charge_enabled,
        post_charge_duration_min=config.post_charge_duration_min,

        # Safety
        emergency_temp_max_c=config.emergency_temp_max_c,
        min_operating_temp_c=config.min_operating_temp_c,
        absolute_min_voltage_mv=config.absolute_min_voltage_mv,
    )


async def write_battery_config(station_id: int, config: BatteryConfig) -> bool:
    """
    Write battery MODEL configuration to EEPROM via I2C.

    Used for programming new dock EEPROMs. Serializes BatteryConfig
    into the v2 binary layout and writes via RP2040.
    """
    try:
        data = bytearray(0x98)  # 152 bytes total

        # --- Header ---
        data[0x00] = config.format_version
        data[0x01] = config.battery_type.value
        _write_u16(data, 0x02, config.nominal_capacity_mah)

        # --- Cell info ---
        data[0x04] = config.cell_count
        data[0x05] = 0  # Reserved
        _write_u16(data, 0x06, config.nominal_voltage_mv)

        # --- Standard charge ---
        _write_u16(data, 0x08, config.charge_voltage_limit_mv)
        _write_u16(data, 0x0A, config.standard_charge_current_ma)
        _write_u16(data, 0x0C, config.standard_charge_duration_min)
        _write_u16(data, 0x0E, config.trickle_charge_current_ma)

        # --- Reconditioning charge ---
        _write_u16(data, 0x10, config.recondition_charge_current_ma)
        _write_u16(data, 0x12, config.recondition_charge_duration_min)
        _write_u16(data, 0x14, config.recondition_storage_threshold_months)
        _write_u16(data, 0x16, 0)  # Reserved

        # --- Capacity test discharge ---
        _write_u16(data, 0x18, config.cap_test_discharge_current_ma)
        _write_u16(data, 0x1A, config.cap_test_end_voltage_mv)
        _write_u16(data, 0x1C, config.cap_test_max_duration_min)
        _write_u16(data, 0x1E, config.cap_test_rest_before_min)

        # --- Capacity pass/fail criteria ---
        _write_u16(data, 0x20, config.cap_test_pass_min_minutes)
        _write_u16(data, 0x22, config.cap_test_pass_min_capacity_pct)
        _write_u16(data, 0x24, config.cap_test_voltage_check_time_min)
        _write_u16(data, 0x26, config.cap_test_voltage_check_min_mv)

        # --- Fast discharge ---
        data[0x28] = 1 if config.fast_discharge_enabled else 0
        data[0x29] = 0  # Reserved
        _write_u16(data, 0x2A, config.fast_discharge_current_ma)
        _write_u16(data, 0x2C, config.fast_discharge_end_voltage_mv)
        _write_u16(data, 0x2E, config.fast_discharge_pass_min_minutes)
        _write_u16(data, 0x30, config.fast_discharge_rest_before_min)
        _write_u16(data, 0x32, 0)  # Reserved

        # --- Pre-discharge ---
        _write_u16(data, 0x34, config.pre_discharge_current_ma)
        _write_u16(data, 0x36, config.pre_discharge_end_voltage_mv)

        # --- Post-charge ---
        data[0x38] = 1 if config.post_charge_enabled else 0
        data[0x39] = 0  # Reserved
        _write_u16(data, 0x3A, config.post_charge_duration_min)

        # --- Temperature limits (deg C x 10, signed) ---
        _write_s16(data, 0x3C, int(config.max_charge_temp_c * 10))
        _write_s16(data, 0x3E, int(config.max_discharge_temp_c * 10))
        _write_s16(data, 0x40, int(config.emergency_temp_max_c * 10))
        _write_s16(data, 0x42, int(config.min_operating_temp_c * 10))

        # --- Safety ---
        _write_u16(data, 0x44, config.absolute_min_voltage_mv)
        _write_u16(data, 0x46, 0)  # Reserved

        # --- Age rest ---
        _write_u16(data, 0x48, config.age_rest_threshold_months)
        _write_u16(data, 0x4A, config.age_rest_duration_min)

        # --- CRC ---
        crc = _crc16(bytes(data[0x00:_CRC_DATA_END]))
        _write_u16(data, _CRC_OFFSET, crc)
        _write_u16(data, 0x4E, 0)  # Reserved

        # --- Strings ---
        _write_string(data, _PART_NUMBER_OFFSET, config.part_number, 32)
        _write_string(data, _MODEL_DESC_OFFSET, config.model_description, 32)
        _write_string(data, _MFG_CODE_OFFSET, config.manufacturer_code, 8)

        # Write via I2C
        success = await i2c_poller.write_eeprom(station_id, bytes(data))
        if success:
            logger.info(f"Station {station_id}: EEPROM written successfully "
                        f"({config.part_number} / {config.model_description})")
        return success

    except Exception as e:
        logger.error(f"Station {station_id}: Failed to write EEPROM: {e}")
        return False


# =============================================================================
# Internal Helpers
# =============================================================================

def _read_u16(data: bytes, offset: int) -> int:
    """Read unsigned 16-bit little-endian value"""
    return (data[offset + 1] << 8) | data[offset]


def _read_s16(data: bytes, offset: int) -> int:
    """Read signed 16-bit little-endian value"""
    value = _read_u16(data, offset)
    if value & 0x8000:
        return value - 0x10000
    return value


def _write_u16(data: bytearray, offset: int, value: int):
    """Write unsigned 16-bit little-endian value"""
    value = max(0, min(65535, value))
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF


def _write_s16(data: bytearray, offset: int, value: int):
    """Write signed 16-bit little-endian value"""
    if value < 0:
        value = value + 0x10000
    _write_u16(data, offset, value)


def _parse_string(data: bytes) -> str:
    """Parse null-terminated string from bytes"""
    try:
        null_index = data.index(0)
        return data[:null_index].decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        return data.decode('utf-8', errors='ignore').rstrip('\x00')


def _write_string(data: bytearray, offset: int, value: str, max_len: int):
    """Write null-terminated string to buffer"""
    encoded = value.encode('utf-8')[:max_len - 1]
    for i, b in enumerate(encoded):
        data[offset + i] = b
    # Rest is already zero-filled from bytearray initialization


def _crc16(data: bytes) -> int:
    """CRC-16/MODBUS for EEPROM data integrity"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc
