"""
Battery Test Bench - Database Models (Service Shop)
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Architecture rewrite — tech pubs as source of truth; data-driven
                      procedures; 8 new tables (tech_pub_applicability, tech_pub_sections,
                      procedure_steps, job_tasks, task_tool_usage, station_equipment,
                      test_reports); column additions to battery_profiles, tools,
                      work_jobs, work_order_items; unified task model replaces
                      work_job_tasks + manual_test_results
v1.3.0 (2026-02-18): Added tech_pubs, tools, station_calibrations, work_jobs,
                      work_job_tasks, task_logs tables; replaced recipes schema;
                      added missing columns to battery_profiles; uses database.py
v1.2.7 (2026-02-16): Added manual_test_results table for non-energy tests;
                      fast_discharge columns in test_records; export ServiceType
v1.2.3 (2026-02-16): Added customer_wo_reference to work_orders table;
                      system records customer's external WO ref, not generates WOs
v1.2.1 (2026-02-16): Service shop schema — customers, work orders, battery profiles,
                      test records, station status, equipment maintenance
v1.0.1 (2026-02-12): Initial database models module
"""

from .station import Station, StationState, BatteryConfig
from .recipe import Recipe, RecipeStep
from .session import Session, SessionData
from .calibration import Calibration
from .config import ConfigKey

import aiosqlite
import logging

logger = logging.getLogger(__name__)


async def _add_column_if_missing(db, table, column, col_type, default=None):
    """Idempotent ALTER TABLE ADD COLUMN"""
    cursor = await db.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in await cursor.fetchall()}
    if column not in existing:
        default_clause = f" DEFAULT {default}" if default is not None else ""
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}")


async def init_db():
    """Initialize SQLite database with service shop schema"""
    from database import get_db_path
    db_path = get_db_path()
    logger.info(f"Initializing database: {db_path}")

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        # ================================================================
        # CUSTOMERS
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                customer_code TEXT UNIQUE,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                country TEXT DEFAULT 'Portugal',
                tax_id TEXT,
                payment_terms TEXT DEFAULT 'Net 30',
                is_active BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # BATTERY PROFILES (test procedures per part number)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battery_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_number TEXT NOT NULL,
                amendment TEXT,
                description TEXT,
                manufacturer TEXT DEFAULT 'DIEHL Aerospace GmbH',

                -- Electrical specs
                nominal_voltage_v REAL NOT NULL,
                capacity_ah REAL NOT NULL,
                num_cells INTEGER NOT NULL,
                chemistry TEXT DEFAULT 'NiCd',

                -- Standard charge (16-hour method)
                std_charge_current_ma INTEGER NOT NULL,
                std_charge_duration_h REAL NOT NULL,
                std_charge_voltage_limit_mv INTEGER NOT NULL,
                std_charge_temp_max_c REAL NOT NULL DEFAULT 45.0,

                -- Capacity test discharge
                cap_test_current_a REAL NOT NULL,
                cap_test_voltage_min_mv INTEGER NOT NULL,
                cap_test_duration_min INTEGER NOT NULL,
                cap_test_temp_max_c REAL NOT NULL DEFAULT 45.0,

                -- Fast charge (optional)
                fast_charge_enabled BOOLEAN DEFAULT 0,
                fast_charge_current_a REAL,
                fast_charge_max_duration_min INTEGER,
                fast_charge_delta_v_mv INTEGER,

                -- Trickle charge
                trickle_charge_current_ma INTEGER,
                trickle_charge_voltage_max_mv INTEGER,

                -- Partial charge (for storage after test)
                partial_charge_duration_h REAL,

                -- Age-based rest period
                rest_period_age_threshold_months INTEGER DEFAULT 24,
                rest_period_duration_h INTEGER DEFAULT 24,

                -- Safety limits
                emergency_temp_max_c REAL DEFAULT 60.0,
                emergency_temp_min_c REAL DEFAULT -20.0,

                is_active BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(part_number, amendment)
            )
        """)

        # Add columns used by mock_server but missing from original schema
        profile_extras = [
            ("manufacturer_code", "TEXT", None),
            ("pre_discharge_current_a", "REAL", None),
            ("pre_discharge_end_voltage_mv", "INTEGER", None),
            ("post_charge_current_ma", "INTEGER", None),
            ("post_charge_duration_h", "REAL", None),
            ("rest_before_cap_test_min", "INTEGER", None),
            ("fast_discharge_enabled", "BOOLEAN", 0),
            ("fast_discharge_current_a", "REAL", None),
            ("fast_discharge_end_voltage_mv", "INTEGER", None),
            ("fast_discharge_duration_min", "INTEGER", None),
            ("discharge_max_temp_c", "REAL", 55.0),
            ("max_temp_c", "REAL", 45.0),
            ("pass_min_minutes", "INTEGER", None),
            ("pass_min_capacity_pct", "INTEGER", None),
        ]
        for col_name, col_type, default in profile_extras:
            await _add_column_if_missing(db, "battery_profiles", col_name, col_type, default)

        # ================================================================
        # WORK ORDERS (jobs from customers)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_number TEXT UNIQUE NOT NULL,
                customer_reference TEXT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                service_type TEXT NOT NULL DEFAULT 'capacity_test',
                priority TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'received',
                received_date TIMESTAMP NOT NULL,
                due_date TIMESTAMP,
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                assigned_technician TEXT,
                customer_notes TEXT,
                technician_notes TEXT,
                estimated_cost REAL,
                actual_cost REAL,
                invoiced BOOLEAN DEFAULT 0,
                invoice_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # WORK ORDER ITEMS (batteries in each work order)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS work_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
                serial_number TEXT NOT NULL,
                part_number TEXT NOT NULL,
                revision TEXT NOT NULL DEFAULT '',
                amendment TEXT,
                profile_id INTEGER REFERENCES battery_profiles(id),
                manufacture_date DATE,
                battery_block_replacement_date DATE,
                age_months INTEGER,
                status TEXT DEFAULT 'pending',
                current_station_id INTEGER,
                current_test_id INTEGER,
                reported_condition TEXT,
                visual_inspection_notes TEXT,
                visual_inspection_passed BOOLEAN,
                result TEXT,
                test_passed BOOLEAN,
                failure_reason TEXT,
                measured_capacity_ah REAL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                testing_started_at TIMESTAMP,
                testing_completed_at TIMESTAMP
            )
        """)

        # ================================================================
        # TEST RECORDS (historical test data)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_item_id INTEGER REFERENCES work_order_items(id),
                battery_serial_number TEXT NOT NULL,
                battery_part_number TEXT NOT NULL,
                battery_amendment TEXT,
                station_id INTEGER NOT NULL,
                dock_serial TEXT,
                test_type TEXT NOT NULL,
                profile_id INTEGER REFERENCES battery_profiles(id),
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                duration_sec INTEGER,
                result TEXT,
                failure_reason TEXT,
                abort_reason TEXT,
                capacity_ah REAL,
                discharge_duration_min REAL,
                max_temp_c REAL,
                max_voltage_v REAL,
                min_voltage_v REAL,
                avg_charge_current_a REAL,
                avg_discharge_current_a REAL,
                -- Fast discharge results (optional)
                fast_discharge_performed BOOLEAN DEFAULT 0,
                fast_discharge_duration_min REAL,
                fast_discharge_capacity_ah REAL,
                fast_discharge_passed BOOLEAN,
                fast_discharge_fail_reason TEXT,

                safety_events_count INTEGER DEFAULT 0,
                thermal_runaway_detected BOOLEAN DEFAULT 0,
                emergency_abort BOOLEAN DEFAULT 0,
                influx_test_id TEXT,
                report_pdf_path TEXT,
                technician_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # STATION STATUS (current state of each bench station)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS station_status (
                station_id INTEGER PRIMARY KEY,
                rp2040_address INTEGER NOT NULL,
                psu_ip_address TEXT NOT NULL,
                load_ip_address TEXT NOT NULL,
                dock_serial TEXT,
                dock_part_number TEXT,
                dock_last_seen TIMESTAMP,
                current_work_order_item_id INTEGER REFERENCES work_order_items(id),
                current_test_id INTEGER REFERENCES test_records(id),
                state TEXT DEFAULT 'idle',
                state_since TIMESTAMP,
                state_progress_pct INTEGER DEFAULT 0,
                is_online BOOLEAN DEFAULT 1,
                is_enabled BOOLEAN DEFAULT 1,
                last_i2c_contact TIMESTAMP,
                error_message TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # EQUIPMENT MAINTENANCE LOG
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS equipment_maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type TEXT NOT NULL,
                equipment_id TEXT NOT NULL,
                maintenance_type TEXT NOT NULL,
                description TEXT,
                performed_by TEXT,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_maintenance_due DATE,
                notes TEXT
            )
        """)

        # ================================================================
        # MANUAL TEST RESULTS (non-energy tests entered via PWA)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS manual_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_item_id INTEGER NOT NULL REFERENCES work_order_items(id),
                test_record_id INTEGER REFERENCES test_records(id),

                -- Insulation test (500VDC megohmmeter, >2 MOhm pass)
                insulation_test_performed BOOLEAN DEFAULT 0,
                insulation_resistance_mohm REAL,
                insulation_test_voltage_vdc INTEGER DEFAULT 500,
                insulation_pass BOOLEAN,

                -- Heating foil resistance (e.g., 14.4 Ohm +/- 20%)
                heating_foil_test_performed BOOLEAN DEFAULT 0,
                heating_foil_resistance_ohm REAL,
                heating_foil_pass BOOLEAN,

                -- Temperature sensor (NTC check)
                temp_sensor_test_performed BOOLEAN DEFAULT 0,
                temp_sensor_resistance_kohm REAL,
                temp_sensor_pass BOOLEAN,

                -- Thermostat test
                thermostat_test_performed BOOLEAN DEFAULT 0,
                thermostat_open_temp_c REAL,
                thermostat_close_temp_c REAL,
                thermostat_pass BOOLEAN,

                -- Visual inspection
                visual_inspection_performed BOOLEAN DEFAULT 0,
                visual_inspection_notes TEXT,
                visual_inspection_pass BOOLEAN,

                -- Weight check
                weight_check_performed BOOLEAN DEFAULT 0,
                weight_kg REAL,
                weight_pass BOOLEAN,

                -- Technician
                technician_name TEXT,
                technician_notes TEXT,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(work_order_item_id, test_record_id)
            )
        """)

        # ================================================================
        # TECH PUBS (Component Maintenance Manuals)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tech_pubs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cmm_number TEXT NOT NULL,
                title TEXT NOT NULL,
                revision TEXT,
                revision_date TEXT,
                applicable_part_numbers TEXT NOT NULL DEFAULT '[]',
                ata_chapter TEXT,
                issued_by TEXT,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # RECIPES (Job Task Templates linked to Tech Pubs / CMM)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tech_pub_id INTEGER REFERENCES tech_pubs(id),
                cmm_reference TEXT,
                name TEXT NOT NULL,
                description TEXT,
                recipe_type TEXT,
                is_default BOOLEAN DEFAULT 0,
                applicable_part_numbers TEXT DEFAULT '[]',
                steps TEXT NOT NULL DEFAULT '[]',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # CALIBRATED TOOLS
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_number TEXT NOT NULL,
                description TEXT,
                manufacturer TEXT,
                serial_number TEXT NOT NULL,
                calibration_date TEXT,
                valid_until TEXT,
                internal_reference TEXT,
                category TEXT,
                is_active BOOLEAN DEFAULT 1,
                calibration_certificate TEXT,
                calibrated_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # STATION CALIBRATIONS (internal PSU + DC Load per dock)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS station_calibrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER NOT NULL,
                unit TEXT NOT NULL CHECK(unit IN ('psu', 'dc_load')),
                model TEXT,
                serial_number TEXT,
                last_calibration_date TEXT,
                next_due_date TEXT,
                calibrated_by TEXT,
                calibration_certificate TEXT,
                result TEXT,
                readings TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(station_id, unit)
            )
        """)

        # ================================================================
        # WORK JOBS (active test sessions)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS work_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER REFERENCES work_orders(id),
                work_order_item_id INTEGER REFERENCES work_order_items(id),
                work_order_number TEXT,
                battery_serial TEXT,
                battery_part_number TEXT,
                battery_amendment TEXT,
                tech_pub_id INTEGER REFERENCES tech_pubs(id),
                tech_pub_cmm TEXT,
                tech_pub_revision TEXT,
                recipe_id INTEGER REFERENCES recipes(id),
                recipe_name TEXT,
                recipe_cmm_ref TEXT,
                station_id INTEGER NOT NULL,
                status TEXT DEFAULT 'in_progress',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                started_by TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # WORK JOB TASKS (immutable task records with chart data)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS work_job_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_job_id INTEGER NOT NULL REFERENCES work_jobs(id) ON DELETE CASCADE,
                task_number INTEGER NOT NULL,
                step_number INTEGER,
                type TEXT NOT NULL,
                label TEXT,
                params TEXT DEFAULT '{}',
                source TEXT DEFAULT 'manual',
                tools_used TEXT DEFAULT '[]',
                measured_values TEXT DEFAULT '{}',
                step_result TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                chart_data TEXT DEFAULT '[]',
                data_points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                result_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # TASK LOGS (per-station manual task history)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                params TEXT DEFAULT '{}',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                chart_data TEXT DEFAULT '[]',
                data_points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # CONFIG (key-value store)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # TECH PUB APPLICABILITY (replaces JSON applicable_part_numbers)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tech_pub_applicability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tech_pub_id INTEGER NOT NULL REFERENCES tech_pubs(id) ON DELETE CASCADE,
                part_number TEXT NOT NULL,
                amendment TEXT DEFAULT '',
                effective_date TEXT,
                notes TEXT,
                UNIQUE(tech_pub_id, part_number, amendment)
            )
        """)

        # ================================================================
        # TECH PUB SECTIONS (ordered inspection/test categories in a CMM)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tech_pub_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tech_pub_id INTEGER NOT NULL REFERENCES tech_pubs(id) ON DELETE CASCADE,
                section_number TEXT NOT NULL,
                title TEXT NOT NULL,
                section_type TEXT NOT NULL CHECK(section_type IN (
                    'inspection','manual_test','automated_test',
                    'evaluation','preparation','completion')),
                description TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_mandatory BOOLEAN DEFAULT 1,
                condition_type TEXT DEFAULT 'always' CHECK(condition_type IN (
                    'always','feature_flag','amendment_match',
                    'age_threshold','service_type','custom_expression')),
                condition_key TEXT,
                condition_value TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tech_pub_id, section_number)
            )
        """)

        # ================================================================
        # PROCEDURE STEPS (atomic units of work within a section)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS procedure_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER NOT NULL REFERENCES tech_pub_sections(id) ON DELETE CASCADE,
                step_number INTEGER NOT NULL,
                step_type TEXT NOT NULL CHECK(step_type IN (
                    'charge','discharge','rest','wait_temp',
                    'measure_resistance','measure_voltage',
                    'measure_weight','measure_temperature',
                    'visual_check','functional_check',
                    'record_value','evaluate_result','operator_action'
                )),
                label TEXT NOT NULL,
                description TEXT,
                param_source TEXT DEFAULT 'fixed' CHECK(param_source IN (
                    'eeprom','profile','fixed','previous_step')),
                param_overrides TEXT DEFAULT '{}',
                pass_criteria_type TEXT CHECK(pass_criteria_type IN (
                    'none','min_value','max_value','range',
                    'min_duration','boolean','expression')),
                pass_criteria_value TEXT,
                measurement_key TEXT,
                measurement_unit TEXT,
                measurement_label TEXT,
                estimated_duration_min REAL DEFAULT 0,
                is_automated BOOLEAN DEFAULT 0,
                requires_tools TEXT DEFAULT '[]',
                condition_type TEXT DEFAULT 'always',
                condition_key TEXT,
                condition_value TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(section_id, step_number)
            )
        """)

        # ================================================================
        # JOB TASKS (unified — replaces work_job_tasks + manual_test_results)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS job_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_job_id INTEGER NOT NULL REFERENCES work_jobs(id) ON DELETE CASCADE,
                parent_task_id INTEGER REFERENCES job_tasks(id),
                section_id INTEGER REFERENCES tech_pub_sections(id),
                step_id INTEGER REFERENCES procedure_steps(id),
                task_number INTEGER NOT NULL,
                step_type TEXT NOT NULL,
                label TEXT NOT NULL,
                description TEXT,
                is_automated BOOLEAN DEFAULT 0,
                source TEXT DEFAULT 'procedure' CHECK(source IN (
                    'procedure','manual','rule_engine')),
                status TEXT DEFAULT 'pending' CHECK(status IN (
                    'pending','skipped','in_progress','paused',
                    'awaiting_input','completed','failed','aborted')),
                params TEXT DEFAULT '{}',
                step_result TEXT CHECK(step_result IN ('pass','fail','info','skipped')),
                measured_values TEXT DEFAULT '{}',
                result_notes TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                chart_data TEXT DEFAULT '[]',
                data_points INTEGER DEFAULT 0,
                influx_query_ref TEXT,
                performed_by TEXT,
                verified_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # TASK TOOL USAGE (proper FK, replaces JSON tools_used)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_task_id INTEGER NOT NULL REFERENCES job_tasks(id) ON DELETE CASCADE,
                tool_id INTEGER NOT NULL REFERENCES tools(id),
                tool_id_display TEXT NOT NULL,
                tool_description TEXT,
                tool_serial_number TEXT NOT NULL,
                tool_calibration_valid BOOLEAN NOT NULL,
                tool_calibration_due TEXT,
                tool_calibration_cert TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # STATION EQUIPMENT (station hardware → tools FK)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS station_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER NOT NULL,
                equipment_role TEXT NOT NULL CHECK(equipment_role IN (
                    'psu','dc_load','rp2040','temp_sensor')),
                tool_id INTEGER REFERENCES tools(id),
                model TEXT,
                serial_number TEXT,
                ip_address TEXT,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(station_id, equipment_role)
            )
        """)

        # ================================================================
        # TEST REPORTS (structured report data for PDF generation)
        # ================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_job_id INTEGER NOT NULL REFERENCES work_jobs(id),
                work_order_item_id INTEGER NOT NULL REFERENCES work_order_items(id),
                battery_serial TEXT NOT NULL,
                battery_part_number TEXT NOT NULL,
                battery_amendment TEXT,
                cmm_number TEXT NOT NULL,
                cmm_revision TEXT,
                cmm_title TEXT,
                customer_name TEXT NOT NULL,
                work_order_number TEXT NOT NULL,
                station_id INTEGER NOT NULL,
                test_started_at TIMESTAMP,
                test_completed_at TIMESTAMP,
                overall_result TEXT NOT NULL CHECK(overall_result IN (
                    'pass','fail','incomplete')),
                result_summary TEXT,
                failure_reasons TEXT DEFAULT '[]',
                station_equipment TEXT DEFAULT '[]',
                tools_used TEXT DEFAULT '[]',
                cap_test_capacity_ah REAL,
                cap_test_capacity_pct REAL,
                cap_test_duration_min REAL,
                cap_test_pass BOOLEAN,
                fast_discharge_performed BOOLEAN DEFAULT 0,
                fast_discharge_capacity_ah REAL,
                fast_discharge_pass BOOLEAN,
                manual_test_summary TEXT DEFAULT '{}',
                pdf_path TEXT,
                pdf_generated BOOLEAN DEFAULT 0,
                technician_name TEXT,
                report_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ================================================================
        # COLUMN ADDITIONS TO EXISTING TABLES (v2.0.0)
        # ================================================================

        # battery_profiles: feature_flags, applicable_manual_tests, tech_pub_id
        await _add_column_if_missing(db, "battery_profiles", "feature_flags",
                                     "TEXT", "'{}'" )
        await _add_column_if_missing(db, "battery_profiles", "applicable_manual_tests",
                                     "TEXT", "'[]'")
        await _add_column_if_missing(db, "battery_profiles", "tech_pub_id",
                                     "INTEGER")

        # tools: tool_id_display (TID format), verification fields, TCP/IP, station
        await _add_column_if_missing(db, "tools", "tool_id_display", "TEXT")
        await _add_column_if_missing(db, "tools", "verification_cycle_days", "INTEGER", 180)
        await _add_column_if_missing(db, "tools", "tcp_ip_address", "TEXT")
        await _add_column_if_missing(db, "tools", "designated_station", "INTEGER")
        await _add_column_if_missing(db, "tools", "verification_date", "TEXT")

        # tech_pubs: manufacturer (alias for issued_by)
        await _add_column_if_missing(db, "tech_pubs", "manufacturer", "TEXT")

        # tech_pub_applicability: service_type
        await _add_column_if_missing(db, "tech_pub_applicability", "service_type", "TEXT", "'inspection_test'")

        # work_orders: internal_work_number
        await _add_column_if_missing(db, "work_orders", "internal_work_number", "TEXT")

        # work_jobs: profile_id, procedure_snapshot, overall_result
        await _add_column_if_missing(db, "work_jobs", "profile_id", "INTEGER")
        await _add_column_if_missing(db, "work_jobs", "procedure_snapshot",
                                     "TEXT", "'{}'")
        await _add_column_if_missing(db, "work_jobs", "overall_result", "TEXT")

        # work_order_items: last_service_date, assigned_tech_pub_id
        await _add_column_if_missing(db, "work_order_items", "last_service_date",
                                     "DATE")
        await _add_column_if_missing(db, "work_order_items", "assigned_tech_pub_id",
                                     "INTEGER")

        # ================================================================
        # INDEXES
        # ================================================================
        # Customers
        await db.execute("CREATE INDEX IF NOT EXISTS idx_customer_code ON customers(customer_code)")
        # Work orders
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wo_number ON work_orders(work_order_number)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wo_customer ON work_orders(customer_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wo_status ON work_orders(status)")
        # Work order items
        await db.execute("CREATE INDEX IF NOT EXISTS idx_woi_work_order ON work_order_items(work_order_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_woi_serial ON work_order_items(serial_number)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_woi_status ON work_order_items(status)")
        # Test records
        await db.execute("CREATE INDEX IF NOT EXISTS idx_test_woi ON test_records(work_order_item_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_test_serial ON test_records(battery_serial_number)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_test_date ON test_records(started_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_test_result ON test_records(result)")
        # Battery profiles
        await db.execute("CREATE INDEX IF NOT EXISTS idx_profile_pn ON battery_profiles(part_number, amendment)")
        # Manual test results
        await db.execute("CREATE INDEX IF NOT EXISTS idx_manual_test_woi ON manual_test_results(work_order_item_id)")
        # Tech pubs
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tp_cmm ON tech_pubs(cmm_number)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tp_active ON tech_pubs(is_active)")
        # Tools
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tool_serial ON tools(serial_number)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_category ON tools(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_valid ON tools(valid_until)")
        # Station calibrations
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sc_station ON station_calibrations(station_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sc_due ON station_calibrations(next_due_date)")
        # Work jobs
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wj_wo ON work_jobs(work_order_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wj_station ON work_jobs(station_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wj_status ON work_jobs(status)")
        # Work job tasks
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wjt_job ON work_job_tasks(work_job_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wjt_status ON work_job_tasks(status)")
        # Task logs
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tl_station ON task_logs(station_id)")
        # Recipes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_recipe_tp ON recipes(tech_pub_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_recipe_type ON recipes(recipe_type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_recipe_active ON recipes(is_active)")
        # Tech pub applicability
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tpa_tp ON tech_pub_applicability(tech_pub_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tpa_pn ON tech_pub_applicability(part_number)")
        # Tech pub sections
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tps_tp ON tech_pub_sections(tech_pub_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tps_type ON tech_pub_sections(section_type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tps_sort ON tech_pub_sections(tech_pub_id, sort_order)")
        # Procedure steps
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ps_section ON procedure_steps(section_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ps_type ON procedure_steps(step_type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ps_sort ON procedure_steps(section_id, sort_order)")
        # Job tasks
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jt_job ON job_tasks(work_job_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jt_status ON job_tasks(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jt_parent ON job_tasks(parent_task_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jt_section ON job_tasks(section_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jt_step ON job_tasks(step_id)")
        # Task tool usage
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ttu_task ON task_tool_usage(job_task_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ttu_tool ON task_tool_usage(tool_id)")
        # Station equipment
        await db.execute("CREATE INDEX IF NOT EXISTS idx_se_station ON station_equipment(station_id)")
        # Test reports
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tr_job ON test_reports(work_job_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tr_woi ON test_reports(work_order_item_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tr_result ON test_reports(overall_result)")

        # ================================================================
        # SEED STATION STATUS (12 stations)
        # ================================================================
        for i in range(1, 13):
            await db.execute("""
                INSERT OR IGNORE INTO station_status
                    (station_id, rp2040_address, psu_ip_address, load_ip_address, state)
                VALUES (?, ?, ?, ?, 'idle')
            """, (i, 0x20 + i - 1, f"192.168.1.{100 + i}", f"192.168.1.{200 + i}"))

        await db.commit()

    logger.info("Database initialized successfully (service shop schema v2.0.0)")


__all__ = [
    'Station', 'StationState', 'BatteryConfig',
    'Recipe', 'RecipeStep',
    'Session', 'SessionData',
    'Calibration', 'ConfigKey',
    'init_db'
]
