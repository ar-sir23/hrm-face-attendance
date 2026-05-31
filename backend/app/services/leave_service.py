from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date, timedelta
import calendar
import logging
from typing import Optional
from app.models.leave_models import (
    LeavePolicy, LeaveBalance, LeaveApplication,
    LeaveType, LeaveStatus, Holiday
)
from app.models.models import Employee

logger = logging.getLogger(__name__)


class LeaveService:

    def create_default_policies(self, db: Session):
        if db.query(LeavePolicy).count() > 0:
            return
        policies = [
            {"leave_type": LeaveType.ANNUAL,    "days_per_year": 18, "carry_forward": True,  "max_carry_days": 5,  "paid": True,  "description": "Annual / Earned Leave"},
            {"leave_type": LeaveType.SICK,       "days_per_year": 14, "carry_forward": False, "max_carry_days": 0,  "paid": True,  "description": "Sick Leave with medical certificate"},
            {"leave_type": LeaveType.CASUAL,     "days_per_year": 10, "carry_forward": False, "max_carry_days": 0,  "paid": True,  "description": "Casual Leave"},
            {"leave_type": LeaveType.MATERNITY,  "days_per_year": 112,"carry_forward": False, "max_carry_days": 0,  "paid": True,  "description": "Maternity Leave (16 weeks)"},
            {"leave_type": LeaveType.PATERNITY,  "days_per_year": 7,  "carry_forward": False, "max_carry_days": 0,  "paid": True,  "description": "Paternity Leave"},
            {"leave_type": LeaveType.EMERGENCY,  "days_per_year": 5,  "carry_forward": False, "max_carry_days": 0,  "paid": True,  "description": "Emergency Leave"},
            {"leave_type": LeaveType.UNPAID,     "days_per_year": 30, "carry_forward": False, "max_carry_days": 0,  "paid": False, "description": "Unpaid Leave"},
        ]
        for p in policies:
            db.add(LeavePolicy(**p))
        db.commit()
        logger.info("Default leave policies created")

    def create_default_holidays(self, db: Session, year: int = None):
        y = year or datetime.now().year
        if db.query(Holiday).filter(
            Holiday.date >= date(y, 1, 1),
            Holiday.date <= date(y, 12, 31)
        ).count() > 0:
            return
        holidays = [
            {"name": "New Year's Day",          "date": date(y, 1, 1)},
            {"name": "International Workers Day","date": date(y, 5, 1)},
            {"name": "Independence Day",         "date": date(y, 3, 26)},
            {"name": "Victory Day",              "date": date(y, 12, 16)},
            {"name": "Eid ul-Fitr Day 1",        "date": date(y, 4, 10), "is_optional": True},
            {"name": "Eid ul-Fitr Day 2",        "date": date(y, 4, 11), "is_optional": True},
            {"name": "Eid ul-Adha Day 1",        "date": date(y, 6, 17), "is_optional": True},
            {"name": "Eid ul-Adha Day 2",        "date": date(y, 6, 18), "is_optional": True},
        ]
        for h in holidays:
            db.add(Holiday(**h))
        db.commit()
        logger.info("Default holidays created for " + str(y))

    def initialize_employee_balance(self, db: Session,
                                     employee_id: int, year: int = None):
        y       = year or datetime.now().year
        policies = db.query(LeavePolicy).filter(
            LeavePolicy.is_active == True
        ).all()
        created = 0
        for policy in policies:
            existing = db.query(LeaveBalance).filter(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year        == y,
                LeaveBalance.leave_type  == policy.leave_type
            ).first()
            if not existing:
                balance = LeaveBalance(
                    employee_id    = employee_id,
                    year           = y,
                    leave_type     = policy.leave_type,
                    total_days     = policy.days_per_year,
                    used_days      = 0,
                    remaining_days = policy.days_per_year
                )
                db.add(balance)
                created += 1
        db.commit()
        return created

    def initialize_all_employees(self, db: Session, year: int = None):
        y         = year or datetime.now().year
        employees = db.query(Employee).filter(Employee.is_active == True).all()
        for emp in employees:
            self.initialize_employee_balance(db, emp.id, y)
        logger.info("Leave balance initialized for " + str(len(employees)) + " employees")

    def calculate_leave_days(self, db: Session,
                              start: date, end: date) -> float:
        holidays = {h.date for h in db.query(Holiday).filter(
            Holiday.date >= start,
            Holiday.date <= end,
            Holiday.is_optional == False
        ).all()}
        total = 0
        current = start
        while current <= end:
            if current.weekday() < 5 and current not in holidays:
                total += 1
            current += timedelta(days=1)
        return float(total)

    def apply_leave(self, db: Session, employee_id: int,
                    leave_type: LeaveType, start_date: date,
                    end_date: date, reason: str,
                    contact_number: str = None,
                    handover_to: str = None) -> dict:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return {"success": False, "message": "Employee not found"}

        if start_date > end_date:
            return {"success": False, "message": "Start date must be before end date"}

        if start_date < date.today():
            return {"success": False, "message": "Cannot apply for past dates"}

        # Check overlap
        overlap = db.query(LeaveApplication).filter(
            LeaveApplication.employee_id == employee_id,
            LeaveApplication.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            LeaveApplication.start_date  <= end_date,
            LeaveApplication.end_date    >= start_date
        ).first()
        if overlap:
            return {"success": False,
                    "message": "Leave already applied for this period"}

        # Calculate days
        total_days = self.calculate_leave_days(db, start_date, end_date)
        if total_days == 0:
            return {"success": False,
                    "message": "No working days in selected period"}

        # Check balance
        year    = start_date.year
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year        == year,
            LeaveBalance.leave_type  == leave_type
        ).first()

        if not balance:
            self.initialize_employee_balance(db, employee_id, year)
            balance = db.query(LeaveBalance).filter(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year        == year,
                LeaveBalance.leave_type  == leave_type
            ).first()

        if balance and balance.remaining_days < total_days:
            return {
                "success":   False,
                "message":   "Insufficient leave balance. Available: " +
                             str(balance.remaining_days) + " days, Required: " +
                             str(total_days) + " days"
            }

        # Create application
        application = LeaveApplication(
            employee_id    = employee_id,
            leave_type     = leave_type,
            start_date     = start_date,
            end_date       = end_date,
            total_days     = total_days,
            reason         = reason,
            contact_number = contact_number,
            handover_to    = handover_to,
            status         = LeaveStatus.PENDING
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        logger.info(emp.full_name + " applied " + str(total_days) +
                    " days " + leave_type.value + " leave")
        return {
            "success":     True,
            "message":     "✅ Leave application submitted successfully",
            "application_id": application.id,
            "total_days":  total_days,
            "status":      "PENDING"
        }

    def approve_leave(self, db: Session, application_id: int,
                      approved_by: str) -> dict:
        app = db.query(LeaveApplication).filter(
            LeaveApplication.id == application_id
        ).first()
        if not app:
            return {"success": False, "message": "Application not found"}
        if app.status != LeaveStatus.PENDING:
            return {"success": False,
                    "message": "Only pending applications can be approved"}

        # Deduct balance
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == app.employee_id,
            LeaveBalance.year        == app.start_date.year,
            LeaveBalance.leave_type  == app.leave_type
        ).first()
        if balance:
            balance.used_days      += app.total_days
            balance.remaining_days -= app.total_days

        app.status      = LeaveStatus.APPROVED
        app.approved_by = approved_by
        app.approved_at = datetime.now()
        db.commit()
        logger.info("Leave approved: application " + str(application_id))
        return {"success": True, "message": "✅ Leave approved!",
                "total_days": app.total_days}

    def reject_leave(self, db: Session, application_id: int,
                     rejected_by: str, reason: str) -> dict:
        app = db.query(LeaveApplication).filter(
            LeaveApplication.id == application_id
        ).first()
        if not app:
            return {"success": False, "message": "Application not found"}
        if app.status != LeaveStatus.PENDING:
            return {"success": False,
                    "message": "Only pending applications can be rejected"}
        app.status        = LeaveStatus.REJECTED
        app.approved_by   = rejected_by
        app.approved_at   = datetime.now()
        app.reject_reason = reason
        db.commit()
        return {"success": True, "message": "Leave rejected"}

    def cancel_leave(self, db: Session, application_id: int,
                     employee_id: int) -> dict:
        app = db.query(LeaveApplication).filter(
            LeaveApplication.id          == application_id,
            LeaveApplication.employee_id == employee_id
        ).first()
        if not app:
            return {"success": False, "message": "Application not found"}
        if app.status == LeaveStatus.APPROVED:
            # Restore balance
            balance = db.query(LeaveBalance).filter(
                LeaveBalance.employee_id == app.employee_id,
                LeaveBalance.year        == app.start_date.year,
                LeaveBalance.leave_type  == app.leave_type
            ).first()
            if balance:
                balance.used_days      -= app.total_days
                balance.remaining_days += app.total_days
        app.status = LeaveStatus.CANCELLED
        db.commit()
        return {"success": True, "message": "Leave cancelled"}

    def get_employee_balance(self, db: Session,
                              employee_id: int, year: int = None) -> list:
        y = year or datetime.now().year
        self.initialize_employee_balance(db, employee_id, y)
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year        == y
        ).all()
        return [
            {
                "leave_type":      b.leave_type.value,
                "total_days":      b.total_days,
                "used_days":       b.used_days,
                "remaining_days":  b.remaining_days,
                "percentage_used": round(
                    (b.used_days / b.total_days * 100)
                    if b.total_days > 0 else 0, 1
                )
            }
            for b in balances
        ]

    def get_pending_applications(self, db: Session) -> list:
        apps = db.query(LeaveApplication).filter(
            LeaveApplication.status == LeaveStatus.PENDING
        ).order_by(LeaveApplication.created_at.desc()).all()
        return [self._format_application(a) for a in apps]

    def get_employee_applications(self, db: Session,
                                   employee_id: int) -> list:
        apps = db.query(LeaveApplication).filter(
            LeaveApplication.employee_id == employee_id
        ).order_by(LeaveApplication.created_at.desc()).all()
        return [self._format_application(a) for a in apps]

    def _format_application(self, app: LeaveApplication) -> dict:
        return {
            "id":           app.id,
            "employee_id":  app.employee.employee_id,
            "employee_name":app.employee.full_name,
            "leave_type":   app.leave_type.value,
            "start_date":   app.start_date.isoformat(),
            "end_date":     app.end_date.isoformat(),
            "total_days":   app.total_days,
            "reason":       app.reason,
            "status":       app.status.value,
            "applied_on":   app.created_at.strftime("%Y-%m-%d %H:%M"),
            "approved_by":  app.approved_by,
            "reject_reason":app.reject_reason
        }


leave_service = LeaveService()
