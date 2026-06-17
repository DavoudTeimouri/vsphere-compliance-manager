from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def run_scheduled_analysis():
    from app.core.database import SessionLocal
    from app.models.models import VCenterConnection, AnalysisRun, AnalysisType, AnalysisStatus
    from app.services.vcenter_service import VCenterService
    from app.services.analysis_engine import AnalysisEngine
    from app.core.security import decrypt_value
    from datetime import datetime

    db = SessionLocal()
    try:
        connections = db.query(VCenterConnection).filter(VCenterConnection.is_active == True).all()
        engine = AnalysisEngine()
        for conn in connections:
            run = AnalysisRun(
                vcenter_id=conn.id,
                analysis_type=AnalysisType.full,
                status=AnalysisStatus.running
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            try:
                password = decrypt_value(conn.encrypted_password)
                svc = VCenterService(conn.host, conn.username, password, conn.port, conn.verify_ssl)
                svc.connect()
                inventory = svc.get_full_inventory()
                svc.disconnect()
                from app.models.models import PatternConfig
                patterns = db.query(PatternConfig).filter(PatternConfig.is_active == True).all()
                pattern_list = [{"pattern_type": p.pattern_type, "regex_pattern": p.regex_pattern} for p in patterns]
                drs = engine.analyze_drs_compliance(inventory, pattern_list)
                storage = engine.analyze_storage_compliance(inventory, pattern_list)
                findings = engine.generate_findings(drs, storage, run.id)
                from app.models.models import AnalysisFinding
                for f in findings:
                    db.add(AnalysisFinding(**f))
                run.status = AnalysisStatus.completed
                run.completed_at = datetime.utcnow()
                run.summary = {"drs": drs.get("summary", {}), "storage": storage.get("summary", {})}
            except Exception as e:
                run.status = AnalysisStatus.failed
                run.error_message = str(e)
                logger.error(f"Scheduled analysis failed for {conn.name}: {e}")
            db.commit()
    finally:
        db.close()

def start_scheduler():
    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.models.models import AppSettings

    db = SessionLocal()
    try:
        setting = db.query(AppSettings).filter(AppSettings.key == "analysis_cron").first()
        cron_expr = setting.plain_value if setting else settings.ANALYSIS_SCHEDULE_CRON
    finally:
        db.close()

    parts = cron_expr.split()
    if len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1],
            day=parts[2], month=parts[3], day_of_week=parts[4]
        )
        scheduler.add_job(run_scheduled_analysis, trigger, id="scheduled_analysis", replace_existing=True)
    scheduler.start()
    logger.info(f"Scheduler started with cron: {cron_expr}")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
