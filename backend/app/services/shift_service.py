from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import Optional, List
import logging
from app.models.shift_models import Shift, EmployeeShift, OvertimeRecord, ShiftType
from app.models.models import Employee, AttendanceSummary, AttendanceStatus

logger = logging.getLogger(__name__)


class ShiftService:

    def create_default_shifts(self, db: Session):
        """Create default factory shifts if none exist"""
        if db.query(Shift).count() > 0:
            return
        default_shifts = [
            {
                "name": "Morning Shift",
                "shift_type": ShiftType.MORNING,
                "start_time": "06:00",
                "end_time": "14:00",
                "late_after": "06:15",
                "grace_minutes": 15,
                "overtime_after_hours": 8,
                "is_night_shift": False
            },
            {
                "name": "Evening Shift",
                "shift_type": ShiftType.EVENING,
                "start_time": "14:00",
                "end_time": "22:00",
                "late_after": "14:15",
                "grace_minutes": 15,
                "overtime_after_hours": 8,
                "is_night_shift": False
            },
            {
                "name": "Night Shift",
                "shift_type": ShiftType.NIGHT,
                "start_time": "22:00",
                "end_time": "06:00",
                "late_after": "22:15",
                "grace_minutes": 15,
                "overtime_after_hours": 8,
                "is_night_shift": True
            },
            {
                "name": "General Shift",
                "shift_type": ShiftType.GENERAL,
                "start_time": "09:00",
                "end_time": "18:00",
                "late_after": "09:30",
                "grace_minutes": 30,
                "overtime_after_hours": 8,
                "is_night_shift": False
            },
        ]
        for s in default_shifts:
            shift = Shift(**s)
            db.add(shift)
        db.commit()
        logger.info("Default shifts created")

    def assign_shift(self, db: Session, employee_id: int, shift_id: int,
                     start_date: date, end_date: Optional[date] = None):
        existing = db.query(EmployeeShift).filter(
            EmployeeShift.employee_id == employee_id,
            EmployeeShift.is_active == True
        ).first()
        if existing:
            existing.is_active = False

        assignment = EmployeeShift(
            employee_id=employee_id,
            shift_id=shift_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        logger.info("Shift assigned: employee " + str(employee_id) + " → shift " + str(shift_id))
        return assignment

    def get_employee_shift(self, db: Session, employee_id: int,
                           target_date: Optional[date] = None) -> Optional[Shift]:
        today = target_date or date.today()
        assignment = db.query(EmployeeShift).filter(
            EmployeeShift.employee_id == employee_id,
            EmployeeShift.is_active == True,
            EmployeeShift.start_date <= today
        ).order_by(EmployeeShift.start_date.desc()).first()
        return assignment.shift if assignment else None

    def calculate_overtime(self, db: Session, employee_id: int,
                           target_date: date) -> Optional[OvertimeRecord]:
        summary = db.query(AttendanceSummary).filter(
            AttendanceSummary.employee_id == employee_id,
            AttendanceSummary.date == target_date
        ).first()
        if not summary or not summary.first_in or not summary.last_out:
            return None

        shift = self.get_employee_shift(db, employee_id, target_date)
        regular_hours   = shift.overtime_after_hours if shift else 8
        actual_hours    = summary.work_hours or 0
        overtime_hours  = max(0, actual_hours - regular_hours)

        existing = db.query(OvertimeRecord).filter(
            OvertimeRecord.employee_id == employee_id,
            OvertimeRecord.date == target_date
        ).first()

        if existing:
            existing.actual_hours   = round(actual_hours, 2)
            existing.overtime_hours = round(overtime_hours, 2)
            existing.shift_id       = shift.id if shift else None
        else:
            record = OvertimeRecord(
                employee_id=employee_id,
                date=target_date,
                shift_id=shift.id if shift else None,
                regular_hours=regular_hours,
                actual_hours=round(actual_hours, 2),
                overtime_hours=round(overtime_hours, 2),
                overtime_rate=150
            )
            db.add(record)

        db.commit()
        return existing or record

    def get_shift_summary(self, db: Session, target_date: date) -> dict:
        shifts = db.query(Shift).filter(Shift.is_active == True).all()
        result = []
        for shift in shifts:
            assignments = db.query(EmployeeShift).filter(
                EmployeeShift.shift_id == shift.id,
                EmployeeShift.is_active == True,
                EmployeeShift.start_date <= target_date
            ).all()
            emp_ids = [a.employee_id for a in assignments]
            present = 0
            if emp_ids:
                present = db.query(AttendanceSummary).filter(
                    AttendanceSummary.employee_id.in_(emp_ids),
                    AttendanceSummary.date == target_date,
                    AttendanceSummary.status != AttendanceStatus.ABSENT
                ).count()
            result.append({
                "shift_id":    shift.id,
                "shift_name":  shift.name,
                "shift_type":  shift.shift_type.value,
                "start_time":  shift.start_time,
                "end_time":    shift.end_time,
                "total_assigned": len(assignments),
                "present_today":  present,
                "absent_today":   len(assignments) - present
            })
        return {
            "date": target_date.isoformat(),
            "shifts": result,
            "total_shifts": len(shifts)
        }

    def get_monthly_overtime(self, db: Session, year: int, month: int) -> list:
        from datetime import date as date_type
        import calendar
        first = date_type(year, month, 1)
        last  = date_type(year, month, calendar.monthrange(year, month)[1])
        records = db.query(OvertimeRecord).filter(
            OvertimeRecord.date >= first,
            OvertimeRecord.date <= last,
            OvertimeRecord.overtime_hours > 0
        ).all()
        result = {}
        for r in records:
            emp_id = r.employee_id
            if emp_id not in result:
                emp = r.employee
                result[emp_id] = {
                    "employee_id":   emp.employee_id,
                    "employee_name": emp.full_name,
                    "total_overtime_hours": 0,
                    "overtime_days": 0,
                    "records": []
                }
            result[emp_id]["total_overtime_hours"] += r.overtime_hours
            result[emp_id]["overtime_days"] += 1
            result[emp_id]["records"].append({
                "date":           r.date.isoformat(),
                "actual_hours":   r.actual_hours,
                "overtime_hours": r.overtime_hours,
                "approved":       r.approved
            })
        return list(result.values())


shift_service = ShiftService()
