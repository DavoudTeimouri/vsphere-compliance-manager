"""
Seed initial data — this runs automatically on startup via lifespan.
You can also run it manually:

    python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.models import User, UserRole, PatternConfig, AppSettings

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # Admin user
    if not db.query(User).filter(User.username == settings.ADMIN_USERNAME).first():
        admin = User(
            username=settings.ADMIN_USERNAME,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            email=settings.ADMIN_EMAIL,
            full_name="Administrator",
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"✓ Admin user '{settings.ADMIN_USERNAME}' created")
        print(f"  Password: {settings.ADMIN_PASSWORD}")
    else:
        print(f"  Admin user '{settings.ADMIN_USERNAME}' already exists")

    # Default patterns
    default_patterns = [
        {"name": "Web Servers",    "pattern_type": "vm_name",   "regex_pattern": r"^(WEB)-"},
        {"name": "App Servers",    "pattern_type": "vm_name",   "regex_pattern": r"^(APP)-"},
        {"name": "DB Servers",     "pattern_type": "vm_name",   "regex_pattern": r"^(DB)-"},
        {"name": "Cache Servers",  "pattern_type": "vm_name",   "regex_pattern": r"^(CACHE)-"},
        {"name": "Proxy Servers",  "pattern_type": "vm_name",   "regex_pattern": r"^(PROXY)-"},
        {"name": "Worker Servers", "pattern_type": "vm_name",   "regex_pattern": r"^(WORKER)-"},
        {"name": "Prod DS",        "pattern_type": "datastore", "regex_pattern": r"^(DS-PROD)-"},
        {"name": "DR DS",          "pattern_type": "datastore", "regex_pattern": r"^(DS-DR)-"},
    ]
    for p in default_patterns:
        if not db.query(PatternConfig).filter(PatternConfig.name == p["name"]).first():
            db.add(PatternConfig(**p, is_active=True))
            print(f"✓ Pattern '{p['name']}' created")

    # Default settings
    for s in [
        {"key": "analysis_cron",   "plain_value": settings.ANALYSIS_SCHEDULE_CRON},
        {"key": "drs_role_prefix", "plain_value": "VCM-AAR"},
        {"key": "app_title",       "plain_value": "vSphere Compliance Manager"},
    ]:
        if not db.query(AppSettings).filter(AppSettings.key == s["key"]).first():
            db.add(AppSettings(**s))

    db.commit()
    print("\n✓ Seed complete")
finally:
    db.close()
