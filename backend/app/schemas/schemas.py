"""
Pydantic schemas for request/response validation.
Keeps API layer clean — models stay as pure DB objects.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime
from app.models.models import UserRole, AnalysisType, AnalysisStatus


# ── Auth ─────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    full_name: Optional[str]

class UserProfile(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: Optional[str]
    role: UserRole
    is_ldap: bool

    class Config:
        from_attributes = True


# ── Users ────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.viewer

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: Optional[str]
    role: UserRole
    is_active: bool
    is_ldap: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── vCenter ──────────────────────────────────────────────

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

class VCenterOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    verify_ssl: bool
    is_active: bool
    version: Optional[str]
    last_connected: Optional[datetime]

    class Config:
        from_attributes = True


# ── Analysis ─────────────────────────────────────────────

class RunAnalysisRequest(BaseModel):
    vcenter_id: int
    analysis_type: AnalysisType = AnalysisType.full

class AnalysisRunOut(BaseModel):
    id: int
    vcenter_id: int
    analysis_type: AnalysisType
    status: AnalysisStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    summary: Optional[Any]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class FindingOut(BaseModel):
    id: int
    finding_type: str
    severity: str
    cluster_name: Optional[str]
    vm_name: Optional[str]
    datastore_name: Optional[str]
    recommendation: Optional[str]
    is_actionable: bool
    action_taken: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Settings ─────────────────────────────────────────────

class SettingUpdate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    description: Optional[str] = None

class PatternCreate(BaseModel):
    name: str
    pattern_type: str
    regex_pattern: str
    description: Optional[str] = None

    @field_validator("regex_pattern")
    @classmethod
    def validate_regex(cls, v: str) -> str:
        import re
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex: {e}")
        return v

class PatternUpdate(BaseModel):
    name: Optional[str] = None
    pattern_type: Optional[str] = None
    regex_pattern: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("regex_pattern")
    @classmethod
    def validate_regex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex: {e}")
        return v


# ── Pagination ───────────────────────────────────────────

class PaginatedResponse(BaseModel):
    data: List[Any]
    meta: dict
