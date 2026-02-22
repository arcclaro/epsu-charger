"""
Battery Test Bench - PDF Report Generation API
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial report generation endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from services import report_generator
from pathlib import Path
from config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{session_id}/generate")
async def generate_report(session_id: int, background_tasks: BackgroundTasks):
    """
    Generate PDF report for a session
    Report generation happens in background, returns immediately
    """
    try:
        # Validate session exists
        from services import data_logger
        session = await data_logger.get_session_detail(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Queue report generation
        background_tasks.add_task(report_generator.generate_report, session_id)

        return {
            "success": True,
            "message": f"Report generation queued for session {session_id}",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue report generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{session_id}/download")
async def download_report(session_id: int):
    """Download generated PDF report"""
    report_path = Path(settings.REPORTS_DIR) / f"session_{session_id}.pdf"

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report not found. Please generate it first using POST /api/reports/{session_id}/generate"
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"battery_test_session_{session_id}.pdf"
    )


@router.get("/{session_id}/status")
async def report_status(session_id: int):
    """Check if report exists for a session"""
    report_path = Path(settings.REPORTS_DIR) / f"session_{session_id}.pdf"

    if report_path.exists():
        return {
            "exists": True,
            "size_bytes": report_path.stat().st_size,
            "modified_at": report_path.stat().st_mtime
        }
    else:
        return {"exists": False}


@router.delete("/{session_id}")
async def delete_report(session_id: int):
    """Delete a generated report"""
    report_path = Path(settings.REPORTS_DIR) / f"session_{session_id}.pdf"

    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"Report not found")

    try:
        report_path.unlink()
        return {"success": True, "message": f"Report deleted for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")
