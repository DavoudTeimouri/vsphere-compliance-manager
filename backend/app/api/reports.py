from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import AnalysisRun, AnalysisFinding, AnalysisStatus
import json, csv, io

router = APIRouter()

@router.get("/")
def list_reports(page: int = 1, per_page: int = 20,
                 db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(AnalysisRun).filter(AnalysisRun.status == AnalysisStatus.completed)
    total = q.count()
    runs = q.order_by(AnalysisRun.started_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    return {"data": [{"id": r.id, "vcenter_id": r.vcenter_id, "analysis_type": r.analysis_type,
                      "started_at": r.started_at, "completed_at": r.completed_at,
                      "summary": r.summary} for r in runs],
            "meta": {"page": page, "per_page": per_page, "total": total}}

@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == report_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Report not found")
    findings = db.query(AnalysisFinding).filter(AnalysisFinding.analysis_run_id == report_id).all()
    return {"id": run.id, "vcenter_id": run.vcenter_id, "analysis_type": run.analysis_type,
            "status": run.status, "started_at": run.started_at, "completed_at": run.completed_at,
            "summary": run.summary,
            "findings": [{"id": f.id, "finding_type": f.finding_type, "severity": f.severity,
                           "cluster_name": f.cluster_name, "vm_name": f.vm_name,
                           "datastore_name": f.datastore_name, "recommendation": f.recommendation,
                           "is_actionable": f.is_actionable, "action_taken": f.action_taken
                           } for f in findings]}

@router.get("/{report_id}/export")
def export_report(report_id: int, format: str = "json",
                  db: Session = Depends(get_db), _=Depends(get_current_user)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == report_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Report not found")
    findings = db.query(AnalysisFinding).filter(AnalysisFinding.analysis_run_id == report_id).all()

    if format == "json":
        data = {"report_id": run.id, "started_at": str(run.started_at),
                "summary": run.summary,
                "findings": [{"type": f.finding_type, "severity": f.severity,
                               "vm": f.vm_name, "cluster": f.cluster_name,
                               "datastore": f.datastore_name,
                               "recommendation": f.recommendation} for f in findings]}
        return Response(content=json.dumps(data, indent=2, default=str),
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.json"})

    elif format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["finding_type", "severity", "cluster_name",
                                                   "vm_name", "datastore_name", "recommendation"])
        writer.writeheader()
        for f in findings:
            writer.writerow({"finding_type": f.finding_type, "severity": f.severity,
                              "cluster_name": f.cluster_name, "vm_name": f.vm_name,
                              "datastore_name": f.datastore_name, "recommendation": f.recommendation})
        return Response(content=buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"})

    raise HTTPException(status_code=400, detail="Supported formats: json, csv")
