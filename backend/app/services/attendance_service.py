from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import Optional
import logging, os, cv2, numpy as np
from app.models.models import Employee, AttendanceLog, AttendanceSummary, AttendanceType, AttendanceStatus
from app.config import settings

logger = logging.getLogger(__name__)

class AttendanceService:
    def record_attendance(self, db, employee_id, confidence, image_data=None, camera_id=None, location=None, method="FACE"):
        try:
            employee = db.query(Employee).filter(
                Employee.employee_id == employee_id,
                Employee.is_active == True
            ).first()
            if not employee:
                return {"success": False, "message": "কর্মী পাওয়া যায়নি"}
            now = datetime.now()
            today = now.date()
            recent = db.query(AttendanceLog).filter(
                AttendanceLog.employee_id == employee.id,
                AttendanceLog.punch_time >= now - timedelta(seconds=settings.DUPLICATE_PUNCH_INTERVAL)
            ).first()
            if recent:
                remaining = settings.DUPLICATE_PUNCH_INTERVAL - int((now - recent.punch_time).total_seconds())
                return {"success": False, "message": f"{remaining} সেকেন্ড পর চেষ্টা করুন"}
            last_log = db.query(AttendanceLog).filter(
                AttendanceLog.employee_id == employee.id,
                func.date(AttendanceLog.punch_time) == today
            ).order_by(AttendanceLog.punch_time.desc()).first()
            punch_type = AttendanceType.IN if (last_log is None or last_log.punch_type == AttendanceType.OUT) else AttendanceType.OUT
            captured_path = None
            if image_data:
                os.makedirs("captured_images", exist_ok=True)
                fname = f"captured_images/{employee_id}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    cv2.imwrite(fname, img)
                    captured_path = fname
            log = AttendanceLog(
                employee_id=employee.id,
                punch_time=now,
                punch_type=punch_type,
                confidence_score=confidence,
                recognition_method=method,
                captured_image_path=captured_path,
                camera_id=camera_id,
                location=location
            )
            db.add(log)
            self._update_summary(db, employee.id, today, punch_type, now)
            db.commit()
            action = "প্রবেশ" if punch_type == AttendanceType.IN else "বাহির"
            return {
                "success": True,
                "employee_id": employee_id,
                "employee_name": employee.full_name,
                "punch_type": punch_type.value,
                "punch_time": now.isoformat(),
                "message": f"✅ {employee.full_name} — {action} ({now.strftime('%H:%M:%S')})"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": str(e)}

    def _update_summary(self, db, emp_id, work_date, punch_type, punch_time):
        summary = db.query(AttendanceSummary).filter(
            AttendanceSummary.employee_id == emp_id,
            AttendanceSummary.date == work_date
        ).first()
        if not summary:
            summary = AttendanceSummary(employee_id=emp_id, date=work_date)
            db.add(summary)
        if punch_type == AttendanceType.IN and not summary.first_in:
            summary.first_in = punch_time
            summary.status = AttendanceStatus.PRESENT
            late_time = datetime.strptime(f"{work_date} {settings.LATE_ARRIVAL_TIME}", "%Y-%m-%d %H:%M")
            if punch_time > late_time:
                summary.is_late = True
                summary.status = AttendanceStatus.LATE
                summary.late_minutes = int((punch_time - late_time).total_seconds() / 60)
        elif punch_type == AttendanceType.OUT:
            summary.last_out = punch_time
            if summary.first_in:
                summary.work_hours = round(
                    (summary.last_out - summary.first_in).total_seconds() / 3600, 2
                )

    def get_today_report(self, db):
        today = date.today()
        summaries = db.query(AttendanceSummary).filter(AttendanceSummary.date == today).all()
        total = db.query(Employee).filter(Employee.is_active == True).count()
        present = sum(1 for s in summaries if s.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE])
        late = sum(1 for s in summaries if s.is_late)
        return {
            "date": today.isoformat(),
            "total_employees": total,
            "present": present,
            "absent": total - present,
            "late": late,
            "present_percentage": round((present / total * 100) if total > 0 else 0, 1)
        }
