from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin, require_operator
from app.core.security import encrypt_value, decrypt_value
from app.models.models import VCenterConnection, User

router = APIRouter()

class VCenterCreate(BaseModel):
    name: str
    host: str
    port: int = 443
    username: str
    password: str
    verify_ssl: bool = False

class VCenterUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: Optional[bool] = None
    is_active: Optional[bool] = None

@router.get("/")
def list_vcenters(db: Session = Depends(get_db), _=Depends(get_current_user)):
    conns = db.query(VCenterConnection).order_by(VCenterConnection.name).all()
    return [{"id": c.id, "name": c.name, "host": c.host, "port": c.port,
             "username": c.username, "verify_ssl": c.verify_ssl,
             "is_active": c.is_active, "version": c.version,
             "last_connected": c.last_connected} for c in conns]

@router.post("/", status_code=201)
def add_vcenter(payload: VCenterCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    conn = VCenterConnection(
        name=payload.name, host=payload.host, port=payload.port,
        username=payload.username,
        encrypted_password=encrypt_value(payload.password),
        verify_ssl=payload.verify_ssl
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return {"id": conn.id, "name": conn.name, "host": conn.host}

@router.put("/{vcenter_id}")
def update_vcenter(vcenter_id: int, payload: VCenterUpdate,
                   db: Session = Depends(get_db), _=Depends(require_admin)):
    conn = db.query(VCenterConnection).filter(VCenterConnection.id == vcenter_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="vCenter not found")
    if payload.name is not None: conn.name = payload.name
    if payload.host is not None: conn.host = payload.host
    if payload.port is not None: conn.port = payload.port
    if payload.username is not None: conn.username = payload.username
    if payload.password is not None: conn.encrypted_password = encrypt_value(payload.password)
    if payload.verify_ssl is not None: conn.verify_ssl = payload.verify_ssl
    if payload.is_active is not None: conn.is_active = payload.is_active
    db.commit()
    return {"id": conn.id, "name": conn.name}

@router.delete("/{vcenter_id}", status_code=204)
def delete_vcenter(vcenter_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    conn = db.query(VCenterConnection).filter(VCenterConnection.id == vcenter_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="vCenter not found")
    db.delete(conn)
    db.commit()

@router.post("/{vcenter_id}/test")
def test_vcenter(vcenter_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    conn = db.query(VCenterConnection).filter(VCenterConnection.id == vcenter_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="vCenter not found")
    try:
        from app.services.vcenter_service import VCenterService
        password = decrypt_value(conn.encrypted_password)
        svc = VCenterService(conn.host, conn.username, password, conn.port, conn.verify_ssl)
        svc.connect()
        version = svc.get_version()
        svc.disconnect()
        conn.version = version
        conn.last_connected = datetime.utcnow()
        db.commit()
        return {"status": "ok", "version": version}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@router.get("/{vcenter_id}/inventory")
def get_inventory(vcenter_id: int, db: Session = Depends(get_db), _=Depends(require_operator)):
    conn = db.query(VCenterConnection).filter(VCenterConnection.id == vcenter_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="vCenter not found")
    try:
        from app.services.vcenter_service import VCenterService
        password = decrypt_value(conn.encrypted_password)
        svc = VCenterService(conn.host, conn.username, password, conn.port, conn.verify_ssl)
        svc.connect()
        inventory = svc.get_full_inventory()
        svc.disconnect()
        return inventory
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
