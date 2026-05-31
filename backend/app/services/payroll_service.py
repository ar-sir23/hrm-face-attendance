from sqlalchemy.orm import Session
from datetime import datetime, date
import calendar
import logging
from app.models.payroll_models import (
    PayrollRecord, EmployeeSalary, SalaryGrade, PayrollStatus
)
from app.models.models import Employee, AttendanceSummary, AttendanceStatus

logger = logging.getLogger(__name__)


class PayrollService:

    def create_default_grades(self, db: Session):
        if db.query(SalaryGrade).count() > 0:
            return
        grades = [
            {"grade_name": "Grade A — Worker",     "basic_salary": 8000,  "house_rent": 2000, "medical": 500,  "transport": 500,  "food": 1000},
            {"grade_name": "Grade B — Sr Worker",  "basic_salary": 10000, "house_rent": 2500, "medical": 750,  "transport": 500,  "food": 1000},
            {"grade_name": "Grade C — Supervisor", "basic_salary": 15000, "house_rent": 4000, "medical": 1000, "transport": 1000, "food": 1500},
            {"grade_name": "Grade D — Manager",    "basic_salary": 25000, "house_rent": 6000, "medical": 2000, "transport": 2000, "food": 2000},
            {"grade_name": "Grade E — Sr Manager", "basic_salary": 40000, "house_rent": 8000, "medical": 3000, "transport": 3000, "food": 2500},
        ]
        for g in grades:
            db.add(SalaryGrade(**g))
        db.commit()
        logger.info("Default salary grades created")

    def set_employee_salary(self, db: Session, employee_id: int,
                             basic_salary: float, house_rent: float = 0,
                             medical: float = 0, transport: float = 0,
                             food: float = 0, overtime_rate: float = 1.5,
                             tax_percentage: float = 0, pf_percentage: float = 0,
                             grade_id: int = None):
        existing = db.query(EmployeeSalary).filter(
            EmployeeSalary.employee_id == employee_id
        ).first()
        if existing:
            existing.basic_salary   = basic_salary
            existing.house_rent     = house_rent
            existing.medical        = medical
            existing.transport      = transport
            existing.food           = food
            existing.overtime_rate  = overtime_rate
            existing.tax_percentage = tax_percentage
            existing.pf_percentage  = pf_percentage
            existing.grade_id       = grade_id
            existing.effective_date = date.today()
        else:
            salary = EmployeeSalary(
                employee_id=employee_id,
                basic_salary=basic_salary,
                house_rent=house_rent,
                medical=medical,
                transport=transport,
                food=food,
                overtime_rate=overtime_rate,
                tax_percentage=tax_percentage,
                pf_percentage=pf_percentage,
                grade_id=grade_id,
                effective_date=date.today()
            )
            db.add(salary)
        db.commit()
        logger.info("Salary set for employee: " + str(employee_id))

    def calculate_payroll(self, db: Session, employee_id: int,
                           year: int, month: int) -> PayrollRecord:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            raise ValueError("Employee not found")

        # Get salary config
        salary_config = db.query(EmployeeSalary).filter(
            EmployeeSalary.employee_id == employee_id,
            EmployeeSalary.is_active == True
        ).first()

        basic       = salary_config.basic_salary  if salary_config else 12000
        house_rent  = salary_config.house_rent    if salary_config else 0
        medical     = salary_config.medical       if salary_config else 0
        transport   = salary_config.transport     if salary_config else 0
        food        = salary_config.food          if salary_config else 0
        ot_rate     = salary_config.overtime_rate if salary_config else 1.5
        tax_pct     = salary_config.tax_percentage if salary_config else 0
        pf_pct      = salary_config.pf_percentage  if salary_config else 0

        # Get attendance
        total_days  = calendar.monthrange(year, month)[1]
        first_day   = date(year, month, 1)
        last_day    = date(year, month, total_days)

        summaries   = db.query(AttendanceSummary).filter(
            AttendanceSummary.employee_id == employee_id,
            AttendanceSummary.date >= first_day,
            AttendanceSummary.date <= last_day
        ).all()

        present     = sum(1 for s in summaries if s.status in [
            AttendanceStatus.PRESENT, AttendanceStatus.LATE])
        absent      = sum(1 for s in summaries if s.status == AttendanceStatus.ABSENT)
        late        = sum(1 for s in summaries if s.is_late)
        total_hours = sum(s.work_hours or 0 for s in summaries)

        # Calculations
        per_day         = basic / total_days
        hourly_rate     = basic / (total_days * 8)
        overtime_hours  = max(0, total_hours - (present * 8))
        overtime_amount = overtime_hours * hourly_rate * ot_rate

        gross_salary    = basic + house_rent + medical + transport + food + overtime_amount

        absent_deduction = absent * per_day
        late_deduction   = late * (per_day * 0.1)
        tax_deduction    = gross_salary * (tax_pct / 100)
        pf_deduction     = basic * (pf_pct / 100)
        total_deduction  = absent_deduction + late_deduction + tax_deduction + pf_deduction

        net_salary = max(0, gross_salary - total_deduction)

        # Save or update record
        record = db.query(PayrollRecord).filter(
            PayrollRecord.employee_id == employee_id,
            PayrollRecord.year  == year,
            PayrollRecord.month == month
        ).first()

        if not record:
            record = PayrollRecord(employee_id=employee_id, year=year, month=month)
            db.add(record)

        record.total_working_days = total_days
        record.present_days       = present
        record.absent_days        = absent
        record.late_days          = late
        record.basic_salary       = round(basic, 2)
        record.house_rent         = round(house_rent, 2)
        record.medical            = round(medical, 2)
        record.transport          = round(transport, 2)
        record.food               = round(food, 2)
        record.overtime_amount    = round(overtime_amount, 2)
        record.gross_salary       = round(gross_salary, 2)
        record.absent_deduction   = round(absent_deduction, 2)
        record.late_deduction     = round(late_deduction, 2)
        record.tax_deduction      = round(tax_deduction, 2)
        record.pf_deduction       = round(pf_deduction, 2)
        record.total_deduction    = round(total_deduction, 2)
        record.net_salary         = round(net_salary, 2)
        record.status             = PayrollStatus.DRAFT

        db.commit()
        db.refresh(record)
        logger.info("Payroll calculated: " + emp.full_name + " " + str(month) + "/" + str(year))
        return record

    def calculate_all_payroll(self, db: Session, year: int, month: int) -> list:
        employees = db.query(Employee).filter(Employee.is_active == True).all()
        results = []
        for emp in employees:
            try:
                record = self.calculate_payroll(db, emp.id, year, month)
                results.append({
                    "employee_id":   emp.employee_id,
                    "employee_name": emp.full_name,
                    "net_salary":    record.net_salary,
                    "status":        record.status.value
                })
            except Exception as e:
                logger.error("Payroll error for " + emp.full_name + ": " + str(e))
        return results

    def get_payroll_record(self, db: Session, employee_id: int,
                            year: int, month: int):
        return db.query(PayrollRecord).filter(
            PayrollRecord.employee_id == employee_id,
            PayrollRecord.year  == year,
            PayrollRecord.month == month
        ).first()

    def approve_payroll(self, db: Session, record_id: int, approved_by: str):
        record = db.query(PayrollRecord).filter(
            PayrollRecord.id == record_id).first()
        if not record:
            raise ValueError("Record not found")
        record.status      = PayrollStatus.APPROVED
        record.approved_by = approved_by
        record.approved_at = datetime.now()
        db.commit()
        return record

    def mark_paid(self, db: Session, record_id: int):
        record = db.query(PayrollRecord).filter(
            PayrollRecord.id == record_id).first()
        if not record:
            raise ValueError("Record not found")
        record.status  = PayrollStatus.PAID
        record.paid_at = datetime.now()
        db.commit()
        return record


payroll_service = PayrollService()
