"""
Battery Test Bench - Main FastAPI Application
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Added procedures and job_tasks API routers;
                      data-driven procedure resolution and orchestration
v1.2.2 (2026-02-16): Added work orders, customers, battery profiles API routers
v1.1.1 (2026-02-12): Updated for I2C register map fix (EVENT_LOG 0x200→0x30)
v1.0.1 (2026-02-12): Focus on PWA backend, firmware interface only
v1.0.0 (2026-02-12): Initial FastAPI application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging
from pathlib import Path

from config import settings, init_directories
from api import stations, recipes, sessions, reports, admin, ws
from api import work_orders, customers, battery_profiles
from api import procedures, job_tasks
from api import tech_pubs, tools as tools_api, work_jobs, station_calibration
from services import i2c_poller, station_manager, data_logger

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{settings.LOGS_DIR}/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Background tasks
background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create necessary directories
    init_directories()

    # Initialize database
    from models import init_db
    await init_db()

    # Start background services
    logger.info("Starting background services...")

    # I2C Polling Service
    i2c_task = asyncio.create_task(i2c_poller.start_polling())
    background_tasks.add(i2c_task)

    # Station Manager Service
    manager_task = asyncio.create_task(station_manager.start_manager())
    background_tasks.add(manager_task)

    # Data Logger Service
    logger_task = asyncio.create_task(data_logger.start_logger())
    background_tasks.add(logger_task)

    logger.info("All services started successfully")

    yield

    # Shutdown
    logger.info("Shutting down services...")

    # Cancel all background tasks
    for task in background_tasks:
        task.cancel()

    # Wait for tasks to complete
    await asyncio.gather(*background_tasks, return_exceptions=True)

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated 12-station battery test bench control system",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(stations.router, prefix="/api/stations", tags=["Stations"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["Recipes"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(ws.router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(work_orders.router, prefix="/api", tags=["Work Orders"])
app.include_router(customers.router, prefix="/api", tags=["Customers"])
app.include_router(battery_profiles.router, prefix="/api", tags=["Battery Profiles"])
app.include_router(procedures.router, prefix="/api", tags=["Procedures"])
app.include_router(job_tasks.router, prefix="/api", tags=["Job Tasks"])
app.include_router(tech_pubs.router, prefix="/api", tags=["Tech Pubs"])
app.include_router(tools_api.router, prefix="/api", tags=["Tools"])
app.include_router(work_jobs.router, prefix="/api", tags=["Work Jobs"])
app.include_router(station_calibration.router, prefix="/api", tags=["Station Calibration"])

# System route aliases — frontend calls /api/system/* not /api/admin/system/*
@app.get("/api/system/info")
async def system_info_alias():
    return await admin.system_info()


@app.get("/api/system/health")
async def system_health_alias():
    return await admin.system_health()


# Serve static files (React build)
frontend_build = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="static")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME
    }


@app.get("/api/status")
async def system_status():
    """System status endpoint"""
    from services.i2c_poller import get_system_status
    return await get_system_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS
    )
