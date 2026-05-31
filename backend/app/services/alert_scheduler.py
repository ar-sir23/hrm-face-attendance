import asyncio
import logging
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Employee, AttendanceSummary, AttendanceStatus
from app.services.email_service import email_service
from app.config import settings

logger = logging.getLogger(__name__)

class AlertScheduler:
    def __init__(self):
        self.running = False
        self.alerted_late    = set()
        self.alerted_absent  = set()
        self.summary_sent    = False
        self.last_reset_date = date.today()

    def reset_daily(self):
        today = date.today()
        if today != self.last_reset_date:
            self.alerted_late.clear()
            self.alerted_absent.clear()
            self.summary_sent    = False
            self.last_reset_date = today
            logger.info("Alert scheduler reset for new day")

    async def check_late_alerts(self):
        if not settings.SEND_LATE_ALERT or not settings.MANAGER_EMAIL:
            return
        db: Session = SessionLocal()
        try:
            today = date.today()
            late_summaries = db.query(AttendanceSummary).filter(
                AttendanceSummary.date == today,
                AttendanceSummary.is_late == True
            ).all()
            for summary in late_summaries:
                emp = summary.employee
                key = emp.employee_id + "_" + str(today)
                if key not in self.alerted_late:
                    arrival = summary.first_in.strftime("%H:%M:%S") if summary.first_in else "Unknown"
                    success = await email_service.send_late_alert(
                        employee_name=emp.full_name,
                        employee_id=emp.employee_id,
                        arrival_time=arrival,
                        late_minutes=summary.late_minutes,
                        manager_email=settings.MANAGER_EMAIL
                    )
                    if success:
                        self.alerted_late.add(key)
                        logger.info("Late alert sent for: " + emp.full_name)
        except Exception as e:
            logger.error("Late alert error: " + str(e))
        finally:
            db.close()

    async def check_absent_alerts(self):
        if not settings.SEND_ABSENT_ALERT or not settings.MANAGER_EMAIL:
            return
        now = datetime.now()
        if now.hour < 11:
            return
        db: Session = SessionLocal()
        try:
            today = date.today()
            all_employees = db.query(Employee).filter(Employee.is_active == True).all()
            present_ids   = {s.employee_id for s in db.query(AttendanceSummary).filter(
                AttendanceSummary.date == today,
                AttendanceSummary.status != AttendanceStatus.ABSENT
            ).all()}
            for emp in all_employees:
                if emp.id not in present_ids:
                    key = emp.employee_id + "_absent_" + str(today)
                    if key not in self.alerted_absent:
                        success = await email_service.send_absent_alert(
                            employee_name=emp.full_name,
                            employee_id=emp.employee_id,
                            manager_email=settings.MANAGER_EMAIL
                        )
                        if success:
                            self.alerted_absent.add(key)
                            logger.info("Absent alert sent for: " + emp.full_name)
        except Exception as e:
            logger.error("Absent alert error: " + str(e))
        finally:
            db.close()

    async def send_daily_summary(self):
        if not settings.SEND_DAILY_SUMMARY or not settings.MANAGER_EMAIL:
            return
        if self.summary_sent:
            return
        now  = datetime.now()
        hour, minute = map(int, settings.DAILY_SUMMARY_TIME.split(":"))
        if now.hour < hour or (now.hour == hour and now.minute < minute):
            return
        db: Session = SessionLocal()
        try:
            today = date.today()
            summaries = db.query(AttendanceSummary).filter(
                AttendanceSummary.date == today).all()
            total   = db.query(Employee).filter(Employee.is_active == True).count()
            present = sum(1 for s in summaries if s.status != AttendanceStatus.ABSENT)
            late    = sum(1 for s in summaries if s.is_late)
            absent  = total - present
            stats   = {
                "total_employees": total,
                "present": present,
                "absent": absent,
                "late": late,
                "present_percentage": round((present/total*100) if total > 0 else 0, 1)
            }
            late_list   = [{"employee_name": s.employee.full_name, "late_minutes": s.late_minutes}
                           for s in summaries if s.is_late]
            absent_list = [{"employee_name": e.full_name}
                           for e in db.query(Employee).filter(Employee.is_active==True).all()
                           if e.id not in {s.employee_id for s in summaries if s.status != AttendanceStatus.ABSENT}]
            success = await email_service.send_daily_summary(
                settings.MANAGER_EMAIL, stats, late_list, absent_list)
            if success:
                self.summary_sent = True
                logger.info("Daily summary sent!")
        except Exception as e:
            logger.error("Daily summary error: " + str(e))
        finally:
            db.close()

    async def run(self):
        self.running = True
        logger.info("Alert scheduler started")
        while self.running:
            self.reset_daily()
            await self.check_late_alerts()
            await self.check_absent_alerts()
            await self.send_daily_summary()
            await asyncio.sleep(300)

alert_scheduler = AlertScheduler()
