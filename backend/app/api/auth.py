from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.deps import get_current_user
from app.models.models import User, UserRole, AuditLog
from app.core.config import settings

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.is_active == True).first()

    # Try LDAP if enabled and user not found locally or is ldap user
    if settings.LDAP_ENABLED and (not user or user.is_ldap):
        try:
            from app.services.ldap_service import LDAPService
            ldap = LDAPService(
                server_url=settings.LDAP_SERVER_URL,
                base_dn=settings.LDAP_BASE_DN,
                bind_dn=settings.LDAP_BIND_DN,
                bind_password=settings.LDAP_BIND_PASSWORD,
                user_search_filter=settings.LDAP_USER_FILTER,
                use_ssl=settings.LDAP_USE_SSL
            )
            ldap_user = ldap.authenticate(payload.username, payload.password)
            if ldap_user:
                role = ldap.map_role_from_groups(ldap_user["groups"], {
                    "admin": settings.LDAP_GROUP_ADMIN,
                    "operator": settings.LDAP_GROUP_OPERATOR
                })
                if not user:
                    user = User(
                        username=payload.username,
                        full_name=ldap_user.get("full_name"),
                        email=ldap_user.get("email"),
                        is_ldap=True,
                        role=UserRole(role)
                    )
                    db.add(user)
                else:
                    user.role = UserRole(role)
                db.commit()
                db.refresh(user)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"LDAP authentication failed: {str(e)}")
    elif not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    log = AuditLog(user_id=user.id, action="login", ip_address=request.client.host)
    db.add(log)
    db.commit()
    return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username, "full_name": user.full_name}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username,
            "full_name": current_user.full_name, "email": current_user.email,
            "role": current_user.role, "is_ldap": current_user.is_ldap}

@router.put("/me/password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    if current_user.is_ldap:
        raise HTTPException(status_code=400, detail="LDAP users cannot change password here")
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
