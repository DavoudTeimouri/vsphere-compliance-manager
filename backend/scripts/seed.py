"""Seed initial data — run once after alembic upgrade head."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.models import User, UserRole, PatternConfig, AppSettings

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Admin user
if not db.query(User).filter(User.username == settings.ADMIN_USERNAME).first():
    admin = User(
        username=settings.ADMIN_USERNAME,
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        email=settings.ADMIN_EMAIL,
        full_name="Administrator",
        role=UserRole.admin,
        is_active=True
    )
    db.add(admin)
    print(f"✓ Admin user '{settings.ADMIN_USERNAME}' created")
else:
    print(f"  Admin user already exists")

# Default patterns
default_patterns = [
    {"name": "Web Servers", "pattern_type": "vm_name",
     "regex_pattern": r"^(WEB)-\d+", "description": "Matches WEB-01, WEB-02, ..."},
    {"name": "App Servers", "pattern_type": "vm_name",
     "regex_pattern": r"^(APP)-\d+", "description": "Matches APP-01, APP-02, ..."},
    {"name": "DB Servers", "pattern_type": "vm_name",
     "regex_pattern": r"^(DB)-\d+", "description": "Matches DB-01, DB-02, ..."},
    {"name": "Production Datastores", "pattern_type": "datastore",
     "regex_pattern": r"^(DS-PROD)-\d+", "description": "Matches DS-PROD-01, DS-PROD-02, ..."},
]
for p in default_patterns:
    if not db.query(PatternConfig).filter(PatternConfig.name == p["name"]).first():
        db.add(PatternConfig(**p, is_active=True))
        print(f"✓ Pattern '{p['name']}' created")

# Default settings
default_settings = [
    {"key": "analysis_cron", "plain_value": "0 2 * * *",
     "description": "Analysis schedule (cron expression)"},
    {"key": "drs_role_prefix", "plain_value": "VCM-AAR",
     "description": "Prefix for VCM-managed DRS anti-affinity rules"},
    {"key": "app_title", "plain_value": "vSphere Compliance Manager",
     "description": "Application display title"},
]
for s in default_settings:
    if not db.query(AppSettings).filter(AppSettings.key == s["key"]).first():
        db.add(AppSettings(**s))
        print(f"✓ Setting '{s['key']}' created")

db.commit()
db.close()
print("\n✓ Seed complete")
