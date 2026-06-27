from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.models import (AnalysisRun, AnalysisFinding, VCenterConnection,
                                AuditLog, User, AnalysisStatus)

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total_vcenters = db.query(VCenterConnection).filter(VCenterConnection.is_active .is_(True)).count()
    total_runs = db.query(AnalysisRun).count()
    last_run = db.query(AnalysisRun).order_by(AnalysisRun.started_at.desc()).first()

    open_findings = db.query(AnalysisFinding).filter(
        AnalysisFinding.action_taken .is_(False),
        AnalysisFinding.is_actionable.is_(True)
    ).count()

    critical = db.query(AnalysisFinding).filter(
        AnalysisFinding.severity == "critical",
        AnalysisFinding.action_taken  .is_(False)
    ).count()

    by_type = db.query(AnalysisFinding.finding_type, func.count(AnalysisFinding.id))\
                .filter(AnalysisFinding.action_taken .is_(False))\
                .group_by(AnalysisFinding.finding_type).all()

    return {
        "total_vcenters": total_vcenters,
        "total_analysis_runs": total_runs,
        "open_findings": open_findings,
        "critical_findings": critical,
        "last_run": {"id": last_run.id, "status": last_run.status,
                     "started_at": last_run.started_at} if last_run else None,
        "findings_by_type": {row[0]: row[1] for row in by_type}
    }

@router.get("/recent-findings")
def recent_findings(db: Session = Depends(get_db), _=Depends(get_current_user)):
    findings = db.query(AnalysisFinding)\
                 .filter(AnalysisFinding.action_taken .is_(False))\
                 .order_by(AnalysisFinding.created_at.desc()).limit(10).all()
    return [{"id": f.id, "finding_type": f.finding_type, "severity": f.severity,
             "vm_name": f.vm_name, "cluster_name": f.cluster_name,
             "recommendation": f.recommendation, "created_at": f.created_at} for f in findings]

@router.get("/audit-log")
def audit_log(page: int = 1, per_page: int = 50,
              db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    total = q.count()
    logs = q.offset((page-1)*per_page).limit(per_page).all()
    return {"data": [{"id": l.id, "user_id": l.user_id, "action": l.action,
                      "resource_type": l.resource_type, "details": l.details,
                      "ip_address": l.ip_address, "created_at": l.created_at} for l in logs],
            "meta": {"page": page, "per_page": per_page, "total": total}}
