from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.security import encrypt_value, decrypt_value
from app.models.models import AppSettings, PatternConfig
import os, shutil

router = APIRouter()

SENSITIVE_KEYS = {"ldap_bind_password", "vcenter_password", "secret_key"}

class SettingUpdate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    description: Optional[str] = None

class PatternCreate(BaseModel):
    name: str
    pattern_type: str  # vm_name | datastore | role
    regex_pattern: str
    description: Optional[str] = None

class PatternUpdate(BaseModel):
    name: Optional[str] = None
    pattern_type: Optional[str] = None
    regex_pattern: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/")
def get_settings(db: Session = Depends(get_db), _=Depends(require_admin)):
    settings = db.query(AppSettings).all()
    result = {}
    for s in settings:
        result[s.key] = {
            "value": "***" if s.is_encrypted else s.plain_value,
            "is_encrypted": s.is_encrypted,
            "description": s.description
        }
    return result

@router.put("/")
def update_settings(payload: List[SettingUpdate], db: Session = Depends(get_db), _=Depends(require_admin)):
    for item in payload:
        setting = db.query(AppSettings).filter(AppSettings.key == item.key).first()
        is_sensitive = item.key in SENSITIVE_KEYS or item.is_encrypted
        if not setting:
            setting = AppSettings(key=item.key, description=item.description)
            db.add(setting)
        setting.is_encrypted = is_sensitive
        setting.description = item.description or setting.description
        if is_sensitive:
            setting.encrypted_value = encrypt_value(item.value)
            setting.plain_value = None
        else:
            setting.plain_value = item.value
            setting.encrypted_value = None
    db.commit()
    return {"updated": len(payload)}

@router.get("/patterns")
def list_patterns(db: Session = Depends(get_db), _=Depends(get_current_user)):
    patterns = db.query(PatternConfig).order_by(PatternConfig.pattern_type, PatternConfig.name).all()
    return [{"id": p.id, "name": p.name, "pattern_type": p.pattern_type,
             "regex_pattern": p.regex_pattern, "description": p.description,
             "is_active": p.is_active} for p in patterns]

@router.post("/patterns", status_code=201)
def create_pattern(payload: PatternCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    import re
    try:
        re.compile(payload.regex_pattern)
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")
    p = PatternConfig(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}

@router.put("/patterns/{pattern_id}")
def update_pattern(pattern_id: int, payload: PatternUpdate,
                   db: Session = Depends(get_db), _=Depends(require_admin)):
    p = db.query(PatternConfig).filter(PatternConfig.id == pattern_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pattern not found")
    if payload.regex_pattern:
        import re
        try:
            re.compile(payload.regex_pattern)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    return {"id": p.id, "name": p.name}

@router.delete("/patterns/{pattern_id}", status_code=204)
def delete_pattern(pattern_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    p = db.query(PatternConfig).filter(PatternConfig.id == pattern_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pattern not found")
    db.delete(p)
    db.commit()

@router.post("/ldap/test")
def test_ldap(db: Session = Depends(get_db), _=Depends(require_admin)):
    from app.core.config import settings as app_settings
    if not app_settings.LDAP_ENABLED:
        raise HTTPException(status_code=400, detail="LDAP is not enabled")
    try:
        from app.services.ldap_service import LDAPService
        svc = LDAPService(app_settings.LDAP_SERVER_URL, app_settings.LDAP_BASE_DN,
                          app_settings.LDAP_BIND_DN, app_settings.LDAP_BIND_PASSWORD,
                          use_ssl=app_settings.LDAP_USE_SSL)
        import ldap as ldap_lib
        conn = ldap_lib.initialize(app_settings.LDAP_SERVER_URL)
        conn.set_option(ldap_lib.OPT_NETWORK_TIMEOUT, 5)
        conn.simple_bind_s(app_settings.LDAP_BIND_DN, app_settings.LDAP_BIND_PASSWORD)
        return {"status": "ok", "message": "LDAP connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"LDAP connection failed: {str(e)}")

@router.post("/logo")
async def upload_logo(file: UploadFile = File(...), _=Depends(require_admin)):
    from app.core.config import settings as app_settings
    allowed = {"image/png", "image/jpeg", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only PNG, JPEG, SVG allowed")
    size = 0
    content = await file.read()
    size = len(content)
    if size > app_settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    ext = file.filename.rsplit(".", 1)[-1]
    logo_path = os.path.join(app_settings.UPLOAD_PATH, f"logo.{ext}")
    os.makedirs(app_settings.UPLOAD_PATH, exist_ok=True)
    with open(logo_path, "wb") as f:
        f.write(content)
    return {"message": "Logo uploaded", "path": f"/uploads/logo.{ext}"}
