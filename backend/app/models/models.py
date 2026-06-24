from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    admin    = "admin"
    operator = "operator"
    viewer   = "viewer"


class AnalysisType(str, enum.Enum):
    drs     = "drs"
    storage = "storage"
    full    = "full"


class AnalysisStatus(str, enum.Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"


# PostgreSQL ENUM types with create_type=False
# The types are created by Alembic migrations, not by create_all().
# This prevents "duplicate key" errors when the DB already exists.
_userrole     = ENUM("admin", "operator", "viewer",
                     name="userrole",     create_type=False)
_analysistype = ENUM("drs", "storage", "full",
                     name="analysistype", create_type=False)
_analysisstatus = ENUM("pending", "running", "completed", "failed",
                       name="analysisstatus", create_type=False)


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(100), unique=True, index=True, nullable=False)
    email           = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name       = Column(String(200))
    role            = Column(_userrole, default="viewer", nullable=False)
    is_active       = Column(Boolean, default=True)
    is_ldap         = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    analyses  = relationship("AnalysisRun", back_populates="triggered_by_user")
    audit_logs = relationship("AuditLog",   back_populates="user")


class VCenterConnection(Base):
    __tablename__ = "vcenter_connections"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(200), nullable=False)
    host              = Column(String(500), nullable=False)
    port              = Column(Integer, default=443)
    username          = Column(String(200), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    verify_ssl        = Column(Boolean, default=False)
    is_active         = Column(Boolean, default=True)
    version           = Column(String(50))
    last_connected    = Column(DateTime(timezone=True))
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    analyses = relationship("AnalysisRun", back_populates="vcenter")


class AppSettings(Base):
    __tablename__ = "app_settings"

    id              = Column(Integer, primary_key=True, index=True)
    key             = Column(String(200), unique=True, nullable=False)
    encrypted_value = Column(Text)
    plain_value     = Column(Text)
    is_encrypted    = Column(Boolean, default=False)
    description     = Column(Text)
    updated_at      = Column(DateTime(timezone=True),
                             onupdate=func.now(), server_default=func.now())


class PatternConfig(Base):
    __tablename__ = "pattern_configs"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(200), nullable=False)
    pattern_type   = Column(String(50))
    regex_pattern  = Column(Text, nullable=False)
    description    = Column(Text)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id            = Column(Integer, primary_key=True, index=True)
    vcenter_id    = Column(Integer, ForeignKey("vcenter_connections.id"))
    triggered_by  = Column(Integer, ForeignKey("users.id"))
    analysis_type = Column(_analysistype, default="full")
    status        = Column(_analysisstatus, default="pending")
    started_at    = Column(DateTime(timezone=True), server_default=func.now())
    completed_at  = Column(DateTime(timezone=True))
    summary       = Column(JSON)
    error_message = Column(Text)

    vcenter             = relationship("VCenterConnection", back_populates="analyses")
    triggered_by_user   = relationship("User",              back_populates="analyses")
    findings            = relationship("AnalysisFinding",   back_populates="analysis_run")


class AnalysisFinding(Base):
    __tablename__ = "analysis_findings"

    id              = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    finding_type    = Column(String(100))
    severity        = Column(String(20))
    cluster_name    = Column(String(500))
    vm_name         = Column(String(500))
    datastore_name  = Column(String(500))
    details         = Column(JSON)
    recommendation  = Column(Text)
    is_actionable   = Column(Boolean, default=False)
    action_taken    = Column(Boolean, default=False)
    action_taken_at = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    analysis_run = relationship("AnalysisRun", back_populates="findings")


class DRSRuleHistory(Base):
    __tablename__ = "drs_rule_history"

    id              = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    cluster_name    = Column(String(500))
    rule_name       = Column(String(500))
    action          = Column(String(50))
    vms_in_rule     = Column(JSON)
    reason          = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class StorageMoveHistory(Base):
    __tablename__ = "storage_move_history"

    id              = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    vm_name         = Column(String(500))
    source_datastore = Column(String(500))
    target_datastore = Column(String(500))
    disk_label      = Column(String(200))
    status          = Column(String(50))
    approved_by     = Column(Integer, ForeignKey("users.id"))
    approved_at     = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"))
    action        = Column(String(200), nullable=False)
    resource_type = Column(String(100))
    resource_id   = Column(String(200))
    details       = Column(JSON)
    ip_address    = Column(String(50))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
