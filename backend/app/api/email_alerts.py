from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models.models import AttendanceSummary, Employee, AttendanceStatus
from app.services.email_service import email_service
from app.services.alert_scheduler import alert_scheduler
from app.config import settings

router = APIRouter()

@router.post("/test")
async def test_email():
    success = await email_service.send_email(
        to_email=settings.MANAGER_EMAIL,
        subject="Test Email — FaceHRM System",
        html_body="<h2>Email is working!</h2><p>Your FaceHRM alert system is configured correctly.</p>"
    )
    return {"success": success, "message": "Test email sent!" if success else "Failed! Check email settings in .env"}

@router.post("/send-late-alerts")
async def send_late_alerts(db: Session = Depends(get_db)):
    today = date.today()
    late  = db.query(AttendanceSummary).filter(
        AttendanceSummary.date == today,
        AttendanceSummary.is_late == True
    ).all()
    sent = 0
    for s in late:
        emp     = s.employee
        arrival = s.first_in.strftime("%H:%M:%S") if s.first_in else "Unknown"
        success = await email_service.send_late_alert(
            emp.full_name, emp.employee_id, arrival,
            s.late_minutes, settings.MANAGER_EMAIL
        )
        if success:
            sent += 1
    return {"sent": sent, "total_late": len(late)}

@router.post("/send-daily-summary")
async def send_summary(db: Session = Depends(get_db)):
    today     = date.today()
    summaries = db.query(AttendanceSummary).filter(AttendanceSummary.date == today).all()
    total     = db.query(Employee).filter(Employee.is_active == True).count()
    present   = sum(1 for s in summaries if s.status != AttendanceStatus.ABSENT)
    stats     = {
        "total_employees": total, "present": present,
        "absent": total - present,
        "late": sum(1 for s in summaries if s.is_late),
        "present_percentage": round((present/total*100) if total > 0 else 0, 1)
    }
    late_list   = [{"employee_name": s.employee.full_name, "late_minutes": s.late_minutes} for s in summaries if s.is_late]
    absent_list = [{"employee_name": e.full_name} for e in db.query(Employee).filter(Employee.is_active==True).all()
                   if e.id not in {s.employee_id for s in summaries if s.status != AttendanceStatus.ABSENT}]
    success = await email_service.send_daily_summary(settings.MANAGER_EMAIL, stats, late_list, absent_list)
    return {"success": success, "message": "Daily summary sent!" if success else "Failed!"}

@router.get("/status")
async def alert_status():
    return {
        "scheduler_running": alert_scheduler.running,
        "manager_email": settings.MANAGER_EMAIL,
        "late_alert_enabled": settings.SEND_LATE_ALERT,
        "absent_alert_enabled": settings.SEND_ABSENT_ALERT,
        "daily_summary_enabled": settings.SEND_DAILY_SUMMARY,
        "daily_summary_time": settings.DAILY_SUMMARY_TIME,
        "alerted_late_today": len(alert_scheduler.alerted_late),
        "alerted_absent_today": len(alert_scheduler.alerted_absent)
    }
