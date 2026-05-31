from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
import calendar
import logging
from typing import Optional
from app.models.models import (
    Employee, AttendanceLog, AttendanceSummary,
    AttendanceType, AttendanceStatus, Department
)
from app.models.payroll_models import PayrollRecord, EmployeeSalary
from app.models.shift_models import EmployeeShift, Shift
from app.models.leave_models import LeaveApplication, LeaveStatus

logger = logging.getLogger(__name__)

# Bangladesh Labour Law 2006 constants
LEGAL_WORK_HOURS_PER_DAY  = 8
LEGAL_WORK_HOURS_PER_WEEK = 48
MAX_OVERTIME_PER_DAY      = 2
MAX_OVERTIME_PER_WEEK     = 12
MIN_WAGE_GARMENTS_2024    = 12500   # BDT — Grade 7 minimum
MATERNITY_LEAVE_DAYS      = 112     # 16 weeks
WEEKLY_HOLIDAY_REQUIRED   = True    # Must have 1 day off per week
ANNUAL_LEAVE_ENTITLEMENT  = 18      # Days per year (1 per 18 working days)


class ComplianceService:

    # ── 1. Labour Law Compliance Check ────────────────────────

    def check_overtime_compliance(self, db: Session,
                                   year: int, month: int) -> dict:
        """Check if overtime limits are followed per Bangladesh Labour Law"""
        first = date(year, month, 1)
        last  = date(year, month, calendar.monthrange(year, month)[1])

        violations     = []
        compliant      = []
        total_employees = db.query(Employee).filter(
            Employee.is_active == True).count()

        employees = db.query(Employee).filter(Employee.is_active == True).all()

        for emp in employees:
            summaries = db.query(AttendanceSummary).filter(
                AttendanceSummary.employee_id == emp.id,
                AttendanceSummary.date >= first,
                AttendanceSummary.date <= last
            ).all()

            for s in summaries:
                if not s.work_hours:
                    continue
                overtime = max(0, s.work_hours - LEGAL_WORK_HOURS_PER_DAY)
                if overtime > MAX_OVERTIME_PER_DAY:
                    violations.append({
                        "employee_id":   emp.employee_id,
                        "employee_name": emp.full_name,
                        "date":          s.date.isoformat(),
                        "work_hours":    round(s.work_hours, 2),
                        "overtime":      round(overtime, 2),
                        "limit":         MAX_OVERTIME_PER_DAY,
                        "violation":     "Daily overtime exceeded " +
                                         str(MAX_OVERTIME_PER_DAY) + " hours"
                    })

        compliance_rate = round(
            ((total_employees - len(violations)) / total_employees * 100)
            if total_employees > 0 else 100, 1)

        return {
            "check":            "Overtime Compliance",
            "law":              "Bangladesh Labour Law 2006 — Section 102",
            "limit":            str(MAX_OVERTIME_PER_DAY) + " hours/day, " +
                                str(MAX_OVERTIME_PER_WEEK) + " hours/week",
            "total_employees":  total_employees,
            "violations":       len(violations),
            "compliant":        total_employees - len(violations),
            "compliance_rate":  compliance_rate,
            "status":           "✅ COMPLIANT" if len(violations) == 0 else "❌ VIOLATIONS FOUND",
            "violation_details":violations[:20]
        }

    def check_minimum_wage_compliance(self, db: Session,
                                       year: int, month: int) -> dict:
        """Check minimum wage compliance"""
        violations = []
        employees  = db.query(Employee).filter(Employee.is_active == True).all()

        for emp in employees:
            salary = db.query(EmployeeSalary).filter(
                EmployeeSalary.employee_id == emp.id,
                EmployeeSalary.is_active   == True
            ).first()

            if salary and salary.basic_salary < MIN_WAGE_GARMENTS_2024:
                violations.append({
                    "employee_id":    emp.employee_id,
                    "employee_name":  emp.full_name,
                    "current_salary": salary.basic_salary,
                    "minimum_wage":   MIN_WAGE_GARMENTS_2024,
                    "shortfall":      MIN_WAGE_GARMENTS_2024 - salary.basic_salary,
                    "violation":      "Salary below minimum wage BDT " +
                                      str(MIN_WAGE_GARMENTS_2024)
                })

        total = len(employees)
        return {
            "check":           "Minimum Wage Compliance",
            "law":             "Minimum Wage Board — Garments Sector 2024",
            "minimum_wage":    "BDT " + str(MIN_WAGE_GARMENTS_2024),
            "total_employees": total,
            "violations":      len(violations),
            "compliant":       total - len(violations),
            "compliance_rate": round(
                ((total - len(violations)) / total * 100)
                if total > 0 else 100, 1),
            "status":          "✅ COMPLIANT" if not violations else "❌ VIOLATIONS",
            "violation_details": violations
        }

    def check_weekly_holiday_compliance(self, db: Session,
                                         year: int, month: int) -> dict:
        """Check if employees got weekly holiday (Friday in Bangladesh)"""
        first      = date(year, month, 1)
        last       = date(year, month, calendar.monthrange(year, month)[1])
        violations = []

        # Get all Fridays in the month
        fridays = []
        current = first
        while current <= last:
            if current.weekday() == 4:   # Friday
                fridays.append(current)
            current += timedelta(days=1)

        employees = db.query(Employee).filter(Employee.is_active == True).all()

        for emp in employees:
            for friday in fridays:
                log = db.query(AttendanceLog).filter(
                    AttendanceLog.employee_id == emp.id,
                    func.date(AttendanceLog.punch_time) == friday
                ).first()
                if log:
                    violations.append({
                        "employee_id":   emp.employee_id,
                        "employee_name": emp.full_name,
                        "date":          friday.isoformat(),
                        "day":           "Friday",
                        "violation":     "Worked on weekly holiday without compensation"
                    })

        total = len(employees)
        return {
            "check":           "Weekly Holiday Compliance",
            "law":             "Bangladesh Labour Law 2006 — Section 103",
            "requirement":     "1 day weekly holiday (Friday)",
            "fridays_checked": len(fridays),
            "total_employees": total,
            "violations":      len(violations),
            "compliance_rate": round(
                ((len(fridays)*total - len(violations)) /
                 (len(fridays)*total) * 100)
                if fridays and total > 0 else 100, 1),
            "status":          "✅ COMPLIANT" if not violations else "⚠️ REVIEW NEEDED",
            "violation_details": violations[:20]
        }

    def check_leave_compliance(self, db: Session, year: int) -> dict:
        """Check leave entitlement compliance"""
        issues    = []
        employees = db.query(Employee).filter(Employee.is_active == True).all()

        for emp in employees:
            approved_leaves = db.query(LeaveApplication).filter(
                LeaveApplication.employee_id == emp.id,
                LeaveApplication.status      == LeaveStatus.APPROVED,
                func.extract("year", LeaveApplication.start_date) == year
            ).count()

            if approved_leaves == 0:
                issues.append({
                    "employee_id":   emp.employee_id,
                    "employee_name": emp.full_name,
                    "issue":         "No leave taken this year — may indicate forced attendance"
                })

        total = len(employees)
        return {
            "check":           "Leave Entitlement Compliance",
            "law":             "Bangladesh Labour Law 2006 — Section 117",
            "entitlement":     str(ANNUAL_LEAVE_ENTITLEMENT) + " days/year",
            "year":            year,
            "total_employees": total,
            "issues_found":    len(issues),
            "compliance_rate": round(
                ((total - len(issues)) / total * 100)
                if total > 0 else 100, 1),
            "status":          "✅ COMPLIANT" if not issues else "⚠️ REVIEW NEEDED",
            "issue_details":   issues[:20]
        }

    # ── 2. Full Compliance Report ──────────────────────────────

    def generate_full_compliance_report(self, db: Session,
                                          year: int, month: int) -> dict:
        """Generate complete compliance report"""
        logger.info("Generating compliance report: " +
                    str(month) + "/" + str(year))

        overtime = self.check_overtime_compliance(db, year, month)
        min_wage = self.check_minimum_wage_compliance(db, year, month)
        holiday  = self.check_weekly_holiday_compliance(db, year, month)
        leave    = self.check_leave_compliance(db, year)

        checks = [overtime, min_wage, holiday, leave]
        total_violations = sum(c.get("violations", 0) +
                               c.get("issues_found", 0) for c in checks)
        overall_rate     = round(
            sum(c.get("compliance_rate", 100) for c in checks) / len(checks), 1)

        return {
            "report_title":      "Labour Law Compliance Report",
            "factory_type":      "Ready Made Garments (RMG)",
            "generated_at":      datetime.now().isoformat(),
            "period":            {
                "year":  year,
                "month": month,
                "month_name": datetime(year, month, 1).strftime("%B %Y")
            },
            "summary": {
                "overall_compliance_rate": overall_rate,
                "total_violations":        total_violations,
                "total_checks":            len(checks),
                "status":                  "✅ FULLY COMPLIANT"
                                           if total_violations == 0
                                           else "⚠️ REQUIRES ATTENTION"
            },
            "checks": {
                "overtime":    overtime,
                "minimum_wage":min_wage,
                "weekly_holiday": holiday,
                "leave_entitlement": leave
            }
        }

    # ── 3. BGMEA Report ────────────────────────────────────────

    def generate_bgmea_report(self, db: Session,
                               year: int, month: int,
                               factory_name: str = "Garments Factory Ltd.",
                               factory_code: str = "BGMEA-0000") -> dict:
        """Generate BGMEA-format workforce report"""
        first = date(year, month, 1)
        last  = date(year, month, calendar.monthrange(year, month)[1])

        employees  = db.query(Employee).filter(Employee.is_active == True).all()
        total_emps = len(employees)

        # Department breakdown
        dept_breakdown = {}
        for emp in employees:
            dept = emp.department.name if emp.department else "Unassigned"
            if dept not in dept_breakdown:
                dept_breakdown[dept] = {"total": 0, "present_avg": 0}
            dept_breakdown[dept]["total"] += 1

        # Attendance stats
        summaries   = db.query(AttendanceSummary).filter(
            AttendanceSummary.date >= first,
            AttendanceSummary.date <= last
        ).all()

        total_days    = calendar.monthrange(year, month)[1]
        working_days  = sum(1 for d in range(total_days)
                            if date(year, month, d+1).weekday() < 5)
        present_count = sum(1 for s in summaries
                            if s.status in [
                                AttendanceStatus.PRESENT,
                                AttendanceStatus.LATE])
        late_count    = sum(1 for s in summaries if s.is_late)
        absent_count  = total_emps * working_days - present_count

        avg_attendance = round(
            (present_count / (total_emps * working_days) * 100)
            if total_emps > 0 and working_days > 0 else 0, 1)

        # Payroll summary
        payroll_records = db.query(PayrollRecord).filter(
            PayrollRecord.year  == year,
            PayrollRecord.month == month
        ).all()

        total_wages = sum(r.net_salary for r in payroll_records)

        # Leave summary
        leaves = db.query(LeaveApplication).filter(
            LeaveApplication.status     == LeaveStatus.APPROVED,
            LeaveApplication.start_date >= first,
            LeaveApplication.end_date   <= last
        ).all()

        return {
            "report_type":    "BGMEA Workforce Compliance Report",
            "factory_name":   factory_name,
            "factory_code":   factory_code,
            "period":         datetime(year, month, 1).strftime("%B %Y"),
            "generated_at":   datetime.now().strftime("%d %B %Y %H:%M"),
            "workforce": {
                "total_workers":       total_emps,
                "working_days":        working_days,
                "avg_attendance_rate": avg_attendance,
                "total_present_days":  present_count,
                "total_absent_days":   absent_count,
                "total_late_days":     late_count,
                "department_breakdown":dept_breakdown
            },
            "wages": {
                "total_wages_paid":   round(total_wages, 2),
                "avg_wage_per_worker":round(
                    total_wages / total_emps if total_emps > 0 else 0, 2),
                "minimum_wage_bdt":   MIN_WAGE_GARMENTS_2024,
                "payroll_records":    len(payroll_records)
            },
            "leave": {
                "total_leave_applications": len(leaves),
                "total_leave_days":         sum(l.total_days for l in leaves)
            },
            "compliance_statement":
                "This factory complies with Bangladesh Labour Law 2006 "
                "and BGMEA regulations regarding working hours, minimum "
                "wages, leave entitlements, and worker welfare."
        }

    # ── 4. Audit Trail ─────────────────────────────────────────

    def get_audit_trail(self, db: Session,
                         start_date: date, end_date: date,
                         employee_id: str = None,
                         action_type: str = None) -> list:
        """Complete audit trail of all attendance actions"""
        query = db.query(AttendanceLog).join(Employee)

        query = query.filter(
            func.date(AttendanceLog.punch_time) >= start_date,
            func.date(AttendanceLog.punch_time) <= end_date
        )

        if employee_id:
            query = query.filter(Employee.employee_id == employee_id)

        if action_type:
            query = query.filter(
                AttendanceLog.punch_type == action_type)

        logs = query.order_by(
            AttendanceLog.punch_time.desc()
        ).limit(500).all()

        return [
            {
                "log_id":        log.id,
                "employee_id":   log.employee.employee_id,
                "employee_name": log.employee.full_name,
                "action":        log.punch_type.value,
                "timestamp":     log.punch_time.isoformat(),
                "method":        log.recognition_method,
                "confidence":    log.confidence_score,
                "location":      log.location,
                "camera_id":     log.camera_id,
                "department":    log.employee.department.name
                                 if log.employee.department else None
            }
            for log in logs
        ]

    def get_suspicious_activities(self, db: Session,
                                   target_date: date) -> list:
        """Detect suspicious attendance patterns"""
        suspicious = []
        employees  = db.query(Employee).filter(Employee.is_active == True).all()

        for emp in employees:
            logs = db.query(AttendanceLog).filter(
                AttendanceLog.employee_id == emp.id,
                func.date(AttendanceLog.punch_time) == target_date
            ).order_by(AttendanceLog.punch_time).all()

            if not logs:
                continue

            # Check 1: Low confidence punches
            low_conf = [l for l in logs
                        if l.confidence_score and
                        l.confidence_score < 70]
            if low_conf:
                suspicious.append({
                    "employee_id":   emp.employee_id,
                    "employee_name": emp.full_name,
                    "type":          "LOW_CONFIDENCE",
                    "severity":      "MEDIUM",
                    "detail":        str(len(low_conf)) +
                                     " low-confidence punches detected",
                    "date":          target_date.isoformat()
                })

            # Check 2: Manual punches (no face recognition)
            manual = [l for l in logs if l.recognition_method == "MANUAL"]
            if manual:
                suspicious.append({
                    "employee_id":   emp.employee_id,
                    "employee_name": emp.full_name,
                    "type":          "MANUAL_PUNCH",
                    "severity":      "LOW",
                    "detail":        str(len(manual)) +
                                     " manual attendance entries",
                    "date":          target_date.isoformat()
                })

            # Check 3: Too many punches in a day
            if len(logs) > 6:
                suspicious.append({
                    "employee_id":   emp.employee_id,
                    "employee_name": emp.full_name,
                    "type":          "EXCESSIVE_PUNCHES",
                    "severity":      "HIGH",
                    "detail":        str(len(logs)) +
                                     " punches in one day (normal: 2-4)",
                    "date":          target_date.isoformat()
                })

        return suspicious


compliance_service = ComplianceService()
