"""
Battery Test Bench - Session History API
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial session history endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models.session import SessionSummary, SessionDetail
from services import data_logger
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/", response_model=List[SessionSummary])
async def get_sessions(
    station_id: Optional[int] = Query(None, ge=1, le=12),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get session history with optional filters
    - station_id: Filter by station (1-12)
    - status: Filter by status (running, completed, failed, aborted)
    - start_date: Filter sessions starting after this date
    - end_date: Filter sessions starting before this date
    - limit: Maximum number of sessions to return
    """
    try:
        sessions = await data_logger.get_sessions(
            station_id=station_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {str(e)}")


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(session_id: int):
    """Get detailed session data including time-series"""
    try:
        session = await data_logger.get_session_detail(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")


@router.get("/{session_id}/export")
async def export_session_csv(session_id: int):
    """Export session data as CSV"""
    from fastapi.responses import StreamingResponse
    import io

    try:
        csv_data = await data_logger.export_session_csv(session_id)
        if not csv_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=session_{session_id}.csv"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")


@router.get("/active/all")
async def get_active_sessions():
    """Get all currently running sessions"""
    try:
        sessions = await data_logger.get_sessions(status="running", limit=12)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active sessions: {str(e)}")
