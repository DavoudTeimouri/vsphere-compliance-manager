from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.deps import get_current_user
from app.core.logging_config import get_logger
from app.models.models import User, UserRole, AuditLog
from app.core.config import settings
from app.schemas.schemas import LoginRequest, TokenResponse, UserProfile

router = APIRouter()
logger = get_logger("auth")


class ChangePasswordRequest:
    def __init__(self, current_password: str, new_password: str):
        self.current_password = current_password
        self.new_password = new_password


from pydantic import BaseModel

class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str


def _do_ldap_login(payload: LoginRequest, db: Session) -> User:
    """Attempt LDAP authentication and return/create the local user."""
    from app.services.ldap_service import LDAPService
    svc = LDAPService(
        server_url=settings.LDAP_SERVER_URL,
        base_dn=settings.LDAP_BASE_DN,
        bind_dn=settings.LDAP_BIND_DN,
        bind_password=settings.LDAP_BIND_PASSWORD,
        user_search_filter=settings.LDAP_USER_FILTER,
        use_ssl=settings.LDAP_USE_SSL,
    )
    ldap_user = svc.authenticate(payload.username, payload.password)
    if not ldap_user:
        raise HTTPException(status_code=401, detail="LDAP: invalid credentials")

    role = svc.map_role_from_groups(ldap_user["groups"], {
        "admin":    settings.LDAP_GROUP_ADMIN,
        "operator": settings.LDAP_GROUP_OPERATOR,
    })

    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        user = User(
            username=payload.username,
            full_name=ldap_user.get("full_name"),
            email=ldap_user.get("email"),
            is_ldap=True,
            role=UserRole(role),
            is_active=True,
        )
        db.add(user)
    else:
        user.role = UserRole(role)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == payload.username,
        User.is_active == True,
    ).first()

    # LDAP path
    if settings.LDAP_ENABLED and (not user or user.is_ldap):
        try:
            user = _do_ldap_login(payload, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("LDAP login error", extra={"error": str(e)})
            raise HTTPException(status_code=401, detail="LDAP authentication failed")

    # Local path
    else:
        if not user:
            logger.warning("Login failed: user not found", extra={"username": payload.username})
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        if not user.hashed_password:
            logger.error("User has no password hash", extra={"username": payload.username})
            raise HTTPException(status_code=401, detail="Account not configured — contact admin")

        if not verify_password(payload.password, user.hashed_password):
            logger.warning("Login failed: wrong password", extra={"username": payload.username})
            raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Issue token
    token = create_access_token({"sub": str(user.id), "role": user.role})

    ip = request.client.host if request.client else "unknown"
    db.add(AuditLog(user_id=user.id, action="login", ip_address=ip))
    db.commit()

    logger.info("Login success", extra={"username": user.username, "role": user.role, "ip": ip})

    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user.role,
        "username":     user.username,
        "full_name":    user.full_name,
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id":        current_user.id,
        "username":  current_user.username,
        "full_name": current_user.full_name,
        "email":     current_user.email,
        "role":      current_user.role,
        "is_ldap":   current_user.is_ldap,
    }


@router.put("/me/password")
def change_password(
    payload: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_ldap:
        raise HTTPException(status_code=400, detail="LDAP users cannot change password here")
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    logger.info("Password changed", extra={"username": current_user.username})
    return {"message": "Password changed successfully"}
