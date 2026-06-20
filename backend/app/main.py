from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import auth, users, vcenter, analysis, reports, settings, dashboard
from app.core.database import engine, Base
from app.core.scheduler import start_scheduler, stop_scheduler


def seed_initial_data():
    """Create admin user and default patterns/settings on first startup."""
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.core.config import settings as cfg
    from app.models.models import User, UserRole, PatternConfig, AppSettings

    db = SessionLocal()
    try:
        # Admin user
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

        # Default patterns
        for p in [
            {"name": "Web Servers",   "pattern_type": "vm_name",   "regex_pattern": r"^(WEB)-"},
            {"name": "App Servers",   "pattern_type": "vm_name",   "regex_pattern": r"^(APP)-"},
            {"name": "DB Servers",    "pattern_type": "vm_name",   "regex_pattern": r"^(DB)-"},
            {"name": "Cache Servers", "pattern_type": "vm_name",   "regex_pattern": r"^(CACHE)-"},
            {"name": "Proxy Servers", "pattern_type": "vm_name",   "regex_pattern": r"^(PROXY)-"},
            {"name": "Worker Servers","pattern_type": "vm_name",   "regex_pattern": r"^(WORKER)-"},
            {"name": "Prod DS",       "pattern_type": "datastore", "regex_pattern": r"^(DS-PROD)-"},
            {"name": "DR DS",         "pattern_type": "datastore", "regex_pattern": r"^(DS-DR)-"},
        ]:
            if not db.query(PatternConfig).filter(PatternConfig.name == p["name"]).first():
                db.add(PatternConfig(**p, is_active=True))

        # Default settings
        for s in [
            {"key": "analysis_cron",   "plain_value": cfg.ANALYSIS_SCHEDULE_CRON},
            {"key": "drs_role_prefix", "plain_value": "VCM-AAR"},
            {"key": "app_title",       "plain_value": "vSphere Compliance Manager"},
        ]:
            if not db.query(AppSettings).filter(AppSettings.key == s["key"]).first():
                db.add(AppSettings(**s))

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="vSphere Compliance Manager",
    description="Enterprise vCenter DRS & Storage Compliance Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(users.router,     prefix="/api/users",     tags=["Users"])
app.include_router(vcenter.router,   prefix="/api/vcenter",   tags=["vCenter"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["Analysis"])
app.include_router(reports.router,   prefix="/api/reports",   tags=["Reports"])
app.include_router(settings.router,  prefix="/api/settings",  tags=["Settings"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
