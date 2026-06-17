from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user, require_operator
from app.core.security import decrypt_value
from app.models.models import (AnalysisRun, AnalysisFinding, AnalysisType, AnalysisStatus,
                                VCenterConnection, PatternConfig, DRSRuleHistory,
                                StorageMoveHistory, User)

router = APIRouter()

class RunAnalysisRequest(BaseModel):
    vcenter_id: int
    analysis_type: AnalysisType = AnalysisType.full

def _do_analysis(run_id: int, vcenter_id: int, analysis_type: AnalysisType):
    from app.core.database import SessionLocal
    from app.services.vcenter_service import VCenterService
    from app.services.analysis_engine import AnalysisEngine

    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        conn = db.query(VCenterConnection).filter(VCenterConnection.id == vcenter_id).first()
        patterns = db.query(PatternConfig).filter(PatternConfig.is_active == True).all()
        pattern_list = [{"pattern_type": p.pattern_type, "regex_pattern": p.regex_pattern} for p in patterns]

        try:
            password = decrypt_value(conn.encrypted_password)
            svc = VCenterService(conn.host, conn.username, password, conn.port, conn.verify_ssl)
            svc.connect()
            inventory = svc.get_full_inventory()
            svc.disconnect()

            engine = AnalysisEngine()
            drs_results = engine.analyze_drs_compliance(inventory, pattern_list) if analysis_type in (AnalysisType.drs, AnalysisType.full) else {}
            storage_results = engine.analyze_storage_compliance(inventory, pattern_list) if analysis_type in (AnalysisType.storage, AnalysisType.full) else {}

            findings = engine.generate_findings(drs_results, storage_results, run_id)
            for f in findings:
                db.add(AnalysisFinding(**f))

            run.status = AnalysisStatus.completed
            run.completed_at = datetime.utcnow()
            run.summary = {
                "drs": {"clusters": len(drs_results.get("clusters", [])),
                        "rules_to_create": drs_results.get("total_rules_to_create", 0),
                        "rules_to_delete": drs_results.get("total_rules_to_delete", 0)},
                "storage": storage_results.get("summary", {})
            }
        except Exception as e:
            run.status = AnalysisStatus.failed
            run.error_message = str(e)
        db.commit()
    finally:
        db.close()

@router.get("/")
def list_runs(page: int = 1, per_page: int = 20, vcenter_id: Optional[int] = None,
              db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(AnalysisRun)
    if vcenter_id:
        q = q.filter(AnalysisRun.vcenter_id == vcenter_id)
    total = q.count()
    runs = q.order_by(AnalysisRun.started_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    return {"data": [{"id": r.id, "vcenter_id": r.vcenter_id, "analysis_type": r.analysis_type,
                      "status": r.status, "started_at": r.started_at,
                      "completed_at": r.completed_at, "summary": r.summary} for r in runs],
            "meta": {"page": page, "per_page": per_page, "total": total}}

@router.post("/run", status_code=202)
def trigger_analysis(payload: RunAnalysisRequest, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
    conn = db.query(VCenterConnection).filter(VCenterConnection.id == payload.vcenter_id,
                                               VCenterConnection.is_active == True).first()
    if not conn:
        raise HTTPException(status_code=404, detail="vCenter not found")
    run = AnalysisRun(vcenter_id=payload.vcenter_id, triggered_by=current_user.id,
                      analysis_type=payload.analysis_type, status=AnalysisStatus.running)
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(_do_analysis, run.id, payload.vcenter_id, payload.analysis_type)
    return {"run_id": run.id, "status": "running"}

@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return {"id": run.id, "vcenter_id": run.vcenter_id, "analysis_type": run.analysis_type,
            "status": run.status, "started_at": run.started_at,
            "completed_at": run.completed_at, "summary": run.summary, "error": run.error_message}

@router.get("/{run_id}/findings")
def get_findings(run_id: int, severity: Optional[str] = None, finding_type: Optional[str] = None,
                 page: int = 1, per_page: int = 50,
                 db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(AnalysisFinding).filter(AnalysisFinding.analysis_run_id == run_id)
    if severity: q = q.filter(AnalysisFinding.severity == severity)
    if finding_type: q = q.filter(AnalysisFinding.finding_type == finding_type)
    total = q.count()
    findings = q.order_by(AnalysisFinding.severity).offset((page-1)*per_page).limit(per_page).all()
    return {"data": [{"id": f.id, "finding_type": f.finding_type, "severity": f.severity,
                      "cluster_name": f.cluster_name, "vm_name": f.vm_name,
                      "datastore_name": f.datastore_name, "details": f.details,
                      "recommendation": f.recommendation, "is_actionable": f.is_actionable,
                      "action_taken": f.action_taken} for f in findings],
            "meta": {"page": page, "per_page": per_page, "total": total}}

@router.post("/{run_id}/apply-drs")
def apply_drs(run_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id,
                                        AnalysisRun.status == AnalysisStatus.completed).first()
    if not run:
        raise HTTPException(status_code=404, detail="Completed analysis run not found")
    conn = db.query(VCenterConnection).filter(VCenterConnection.id == run.vcenter_id).first()
    try:
        from app.services.vcenter_service import VCenterService
        password = decrypt_value(conn.encrypted_password)
        svc = VCenterService(conn.host, conn.username, password, conn.port, conn.verify_ssl)
        svc.connect()
        clusters = svc.get_all_clusters()
        cluster_map = {c.name: c for c in clusters}

        findings = db.query(AnalysisFinding).filter(
            AnalysisFinding.analysis_run_id == run_id,
            AnalysisFinding.finding_type == "drs_rule_needed",
            AnalysisFinding.action_taken == False
        ).all()

        created, failed = 0, 0
        for finding in findings:
            details = finding.details or {}
            cluster_name = finding.cluster_name
            cluster = cluster_map.get(cluster_name)
            if not cluster:
                continue
            # Delete old VCM rules first (from details)
            success = svc.create_anti_affinity_rule(cluster, details["rule_name"], details["vms"])
            if success:
                finding.action_taken = True
                finding.action_taken_at = datetime.utcnow()
                db.add(DRSRuleHistory(analysis_run_id=run_id, cluster_name=cluster_name,
                                      rule_name=details["rule_name"], action="created",
                                      vms_in_rule=details["vms"],
                                      reason=f"Applied by {current_user.username}"))
                created += 1
            else:
                failed += 1
        svc.disconnect()
        db.commit()
        return {"created": created, "failed": failed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{run_id}/approve-storage/{finding_id}")
def approve_storage_move(run_id: int, finding_id: int,
                         db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
    finding = db.query(AnalysisFinding).filter(
        AnalysisFinding.id == finding_id,
        AnalysisFinding.analysis_run_id == run_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    move = StorageMoveHistory(
        analysis_run_id=run_id, vm_name=finding.vm_name,
        source_datastore=finding.datastore_name,
        target_datastore=finding.details.get("recommendation", ""),
        status="approved", approved_by=current_user.id,
        approved_at=datetime.utcnow()
    )
    db.add(move)
    finding.action_taken = True
    finding.action_taken_at = datetime.utcnow()
    db.commit()
    return {"message": "Storage move approved and logged", "move_id": move.id}
