"""
Battery Test Bench - PDF Report Generator Service
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Rewritten to read from test_reports + job_tasks tables.
                      Structured CMM-compliant reports with: CMM reference,
                      battery ID, manual test results, equipment list with TIDs,
                      pass/fail summary, V/I/T curves from chart_data.
v1.0.1 (2026-02-12): Initial PDF report generator
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from config import settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import aiosqlite

logger = logging.getLogger(__name__)


async def generate_report(work_job_id: int) -> str:
    """
    Generate a CMM-compliant PDF report for a completed work job.

    Reads structured data from test_reports and job_tasks tables.
    Returns the path to the generated PDF.
    """
    logger.info(f"Generating report for work_job {work_job_id}")

    try:
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Get test report data
            cursor = await db.execute(
                "SELECT * FROM test_reports WHERE work_job_id = ?",
                (work_job_id,))
            report = await cursor.fetchone()

            if not report:
                # Fallback: generate report data from job_tasks directly
                report = await _build_report_from_tasks(db, work_job_id)
                if not report:
                    logger.error(f"No report data for job {work_job_id}")
                    return ""

            # Get all job tasks
            cursor = await db.execute("""
                SELECT * FROM job_tasks
                WHERE work_job_id = ?
                ORDER BY task_number ASC
            """, (work_job_id,))
            tasks = await cursor.fetchall()

        # Build PDF
        report_dir = Path(settings.REPORTS_DIR)
        report_dir.mkdir(parents=True, exist_ok=True)

        wo_num = report["work_order_number"]
        serial = report["battery_serial"]
        pdf_name = f"report_{wo_num}_{serial}_{work_job_id}.pdf"
        pdf_path = report_dir / pdf_name

        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []

        # -- Title --
        story.append(Paragraph(
            "<b>Battery Test Report</b>", styles['Title']))
        story.append(Spacer(1, 0.1 * inch))

        # -- CMM Reference Header --
        cmm_text = (
            f"<b>CMM:</b> {report['cmm_number']} — {report['cmm_title']}<br/>"
            f"<b>Revision:</b> {report['cmm_revision']}<br/>"
        )
        story.append(Paragraph(cmm_text, styles['Normal']))
        story.append(Spacer(1, 0.15 * inch))

        # -- Battery & Work Order Info --
        info_data = [
            ["Work Order", report["work_order_number"]],
            ["Customer", report["customer_name"]],
            ["Battery Serial", report["battery_serial"]],
            ["Part Number", report["battery_part_number"]],
            ["Amendment", report["battery_amendment"] or "—"],
            ["Station", str(report["station_id"])],
            ["Test Started", report["test_started_at"] or "—"],
            ["Test Completed", report["test_completed_at"] or "—"],
            ["Technician", report["technician_name"] or "—"],
            ["Overall Result", report["overall_result"].upper()],
        ]
        info_table = Table(info_data, colWidths=[1.8*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.2 * inch))

        # -- Task Results Summary --
        story.append(Paragraph("<b>Test Steps</b>", styles['Heading2']))
        task_header = ["#", "Step", "Type", "Result", "Duration", "Notes"]
        task_rows = [task_header]
        for t in tasks:
            if t["parent_task_id"] is not None:
                # Indent child tasks
                label = f"  {t['label']}"
            else:
                label = t["label"]
            duration = ""
            if t["start_time"] and t["end_time"]:
                try:
                    s = datetime.fromisoformat(t["start_time"])
                    e = datetime.fromisoformat(t["end_time"])
                    mins = (e - s).total_seconds() / 60
                    duration = f"{mins:.0f} min"
                except (ValueError, TypeError):
                    pass
            result = (t["step_result"] or "—").upper()
            task_rows.append([
                str(t["task_number"]),
                label[:40],
                t["step_type"],
                result,
                duration,
                (t["result_notes"] or "")[:50],
            ])

        task_table = Table(task_rows, colWidths=[
            0.4*inch, 2.2*inch, 1.0*inch, 0.6*inch, 0.8*inch, 1.3*inch])
        task_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.5)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(task_table)
        story.append(Spacer(1, 0.2 * inch))

        # -- V/I/T Curves --
        plot_path = await _generate_plots(tasks, work_job_id)
        if plot_path and plot_path.exists():
            story.append(Paragraph("<b>Charge/Discharge Curves</b>",
                                   styles['Heading2']))
            img = Image(str(plot_path), width=6.5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))

        # -- Equipment & Tools --
        tools_used = json.loads(report["tools_used"] or "[]")
        equipment = json.loads(report["station_equipment"] or "[]")

        if tools_used or equipment:
            story.append(Paragraph("<b>Equipment & Calibrated Tools</b>",
                                   styles['Heading2']))

        if equipment:
            eq_header = ["Role", "Model", "Serial", "IP"]
            eq_rows = [eq_header]
            for eq in equipment:
                eq_rows.append([
                    eq.get("equipment_role", ""),
                    eq.get("model", ""),
                    eq.get("serial_number", ""),
                    eq.get("ip_address", ""),
                ])
            eq_table = Table(eq_rows, colWidths=[1.0*inch, 1.8*inch, 2.0*inch, 1.5*inch])
            eq_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.5)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(eq_table)
            story.append(Spacer(1, 0.1 * inch))

        if tools_used:
            tool_header = ["TID", "Description", "Serial", "Cal. Cert"]
            tool_rows = [tool_header]
            for tool in tools_used:
                tool_rows.append([
                    tool.get("tool_id_display", ""),
                    tool.get("tool_description", tool.get("description", "")),
                    tool.get("tool_serial_number", tool.get("serial_number", "")),
                    tool.get("tool_calibration_cert",
                             tool.get("calibration_cert", "")),
                ])
            tool_table = Table(tool_rows, colWidths=[0.7*inch, 2.5*inch, 1.8*inch, 1.3*inch])
            tool_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.5)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(tool_table)
            story.append(Spacer(1, 0.2 * inch))

        # -- Failure Reasons (if any) --
        failures = json.loads(report["failure_reasons"] or "[]")
        if failures:
            story.append(Paragraph("<b>Failure Details</b>", styles['Heading2']))
            for f in failures:
                story.append(Paragraph(
                    f"- <b>{f.get('step', '')}</b>: {f.get('reason', '')}",
                    styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

        # -- Result Summary --
        result_color = "green" if report["overall_result"] == "pass" else "red"
        story.append(Paragraph(
            f"<b>OVERALL RESULT: <font color='{result_color}'>"
            f"{report['overall_result'].upper()}</font></b>",
            styles['Heading1']))

        # Build PDF
        doc.build(story)

        # Update test_reports with PDF path
        async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
            await db.execute("""
                UPDATE test_reports SET pdf_path = ?, pdf_generated = 1,
                       report_generated_at = ?
                WHERE work_job_id = ?
            """, (str(pdf_path), datetime.now().isoformat(), work_job_id))
            await db.commit()

        logger.info(f"Report generated: {pdf_path}")
        return str(pdf_path)

    except Exception as e:
        logger.error(f"Failed to generate report for job {work_job_id}: {e}",
                     exc_info=True)
        return ""


async def _build_report_from_tasks(db, work_job_id: int):
    """Build report data directly from work_jobs + job_tasks when no test_reports row exists."""
    cursor = await db.execute("""
        SELECT wj.*, wo.work_order_number, c.name as customer_name,
               tp.cmm_number, tp.revision as cmm_revision, tp.title as cmm_title
        FROM work_jobs wj
        JOIN work_orders wo ON wj.work_order_id = wo.id
        JOIN customers c ON wo.customer_id = c.id
        LEFT JOIN tech_pubs tp ON wj.tech_pub_id = tp.id
        WHERE wj.id = ?
    """, (work_job_id,))
    job = await cursor.fetchone()
    if not job:
        return None

    # Build a dict that matches test_reports schema
    return {
        "work_job_id": work_job_id,
        "work_order_item_id": job["work_order_item_id"],
        "battery_serial": job["battery_serial"],
        "battery_part_number": job["battery_part_number"],
        "battery_amendment": job["battery_amendment"],
        "cmm_number": job["cmm_number"] or "",
        "cmm_revision": job["cmm_revision"] or "",
        "cmm_title": job["cmm_title"] or "",
        "customer_name": job["customer_name"],
        "work_order_number": job["work_order_number"],
        "station_id": job["station_id"],
        "test_started_at": job["started_at"],
        "test_completed_at": job["completed_at"],
        "overall_result": job.get("overall_result") or job.get("result") or "incomplete",
        "failure_reasons": "[]",
        "station_equipment": "[]",
        "tools_used": "[]",
        "technician_name": job.get("started_by", ""),
    }


async def _generate_plots(tasks, work_job_id: int):
    """Generate V/I/T plots from job_tasks chart_data."""
    try:
        # Collect chart data from automated tasks
        all_times = []
        all_voltages = []
        all_currents = []
        all_temps = []
        time_offset = 0

        for t in tasks:
            chart_data = json.loads(t["chart_data"] or "[]")
            if not chart_data:
                continue
            for point in chart_data:
                all_times.append((point.get("t", 0) + time_offset) / 3600.0)
                all_voltages.append(point.get("V", 0) / 1000.0)
                all_currents.append(point.get("I", 0) / 1000.0)
                all_temps.append(point.get("T", 0))
            if chart_data:
                time_offset += chart_data[-1].get("t", 0)

        if not all_times:
            return None

        report_dir = Path(settings.REPORTS_DIR)
        report_dir.mkdir(parents=True, exist_ok=True)
        plot_path = report_dir / f"job_{work_job_id}_curves.png"

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 7), sharex=True)

        ax1.plot(all_times, all_voltages, 'b-', linewidth=0.8)
        ax1.set_ylabel('Voltage (V)', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)

        ax2.plot(all_times, all_currents, 'r-', linewidth=0.8)
        ax2.set_ylabel('Current (A)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        ax2.grid(True, alpha=0.3)

        ax3.plot(all_times, all_temps, 'g-', linewidth=0.8)
        ax3.set_ylabel('Temperature (C)', color='g')
        ax3.set_xlabel('Time (hours)')
        ax3.tick_params(axis='y', labelcolor='g')
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(plot_path, dpi=getattr(settings, 'REPORT_DPI', 150))
        plt.close()

        return plot_path

    except Exception as e:
        logger.error(f"Failed to generate plots: {e}")
        return None
