from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.api import auth, users, vcenter, analysis, reports, settings, dashboard
from app.core.database import engine, Base
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("main")


def seed_initial_data() -> None:
    """Create admin user and default patterns/settings on first startup."""
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.core.config import settings as cfg
    from app.models.models import User, UserRole, PatternConfig, AppSettings

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == cfg.ADMIN_USERNAME).first():
            db.add(User(
                username=cfg.ADMIN_USERNAME,
                hashed_password=get_password_hash(cfg.ADMIN_PASSWORD),
                email=cfg.ADMIN_EMAIL,
                full_name="Administrator",
                role=UserRole.admin,
                is_active=True,
            ))
            db.commit()
            logger.info("Admin user created", extra={"username": cfg.ADMIN_USERNAME})

        patterns = [
            {"name": "Web Servers",    "pattern_type": "vm_name",   "regex_pattern": r"^(WEB)-"},
            {"name": "App Servers",    "pattern_type": "vm_name",   "regex_pattern": r"^(APP)-"},
            {"name": "DB Servers",     "pattern_type": "vm_name",   "regex_pattern": r"^(DB)-"},
            {"name": "Cache Servers",  "pattern_type": "vm_name",   "regex_pattern": r"^(CACHE)-"},
            {"name": "Proxy Servers",  "pattern_type": "vm_name",   "regex_pattern": r"^(PROXY)-"},
            {"name": "Worker Servers", "pattern_type": "vm_name",   "regex_pattern": r"^(WORKER)-"},
            {"name": "Prod DS",        "pattern_type": "datastore", "regex_pattern": r"^(DS-PROD)-"},
            {"name": "DR DS",          "pattern_type": "datastore", "regex_pattern": r"^(DS-DR)-"},
        ]
        for p in patterns:
            if not db.query(PatternConfig).filter(PatternConfig.name == p["name"]).first():
                db.add(PatternConfig(**p, is_active=True))

        for s in [
            {"key": "analysis_cron",   "plain_value": "0 2 * * *"},
            {"key": "drs_role_prefix", "plain_value": "VCM-AAR"},
            {"key": "app_title",       "plain_value": "vSphere Compliance Manager"},
        ]:
            if not db.query(AppSettings).filter(AppSettings.key == s["key"]).first():
                db.add(AppSettings(**s))

        db.commit()
        logger.info("Seed complete")
    except Exception as e:
        logger.error("Seed failed", extra={"error": str(e)})
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VCM starting up")
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    start_scheduler()
    logger.info("VCM ready")
    yield
    stop_scheduler()
    logger.info("VCM shut down")


app = FastAPI(
    title="vSphere Compliance Manager",
    description="Enterprise vCenter DRS & Storage Compliance Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with timing."""
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    logger.info(
        "HTTP",
        extra={
            "method":   request.method,
            "path":     request.url.path,
            "status":   response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", extra={
        "path":  request.url.path,
        "error": str(exc),
    })
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(users.router,     prefix="/api/users",     tags=["Users"])
app.include_router(vcenter.router,   prefix="/api/vcenter",   tags=["vCenter"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["Analysis"])
app.include_router(reports.router,   prefix="/api/reports",   tags=["Reports"])
app.include_router(settings.router,  prefix="/api/settings",  tags=["Settings"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
