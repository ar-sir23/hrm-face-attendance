from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
import io
from app.database import get_db
from app.models.payroll_models import (
    PayrollRecord, EmployeeSalary, SalaryGrade, PayrollStatus
)
from app.models.models import Employee
from app.services.payroll_service import payroll_service
from app.services.payslip_service import payslip_service

router = APIRouter()


class SalarySet(BaseModel):
    employee_id:    str
    basic_salary:   float
    house_rent:     float = 0
    medical:        float = 0
    transport:      float = 0
    food:           float = 0
    overtime_rate:  float = 1.5
    tax_percentage: float = 0
    pf_percentage:  float = 0
    grade_id:       Optional[int] = None


class PayrollApprove(BaseModel):
    approved_by: str


# ── Salary Grades ──────────────────────────────────────────────

@router.post("/grades/create-defaults")
async def create_default_grades(db: Session = Depends(get_db)):
    payroll_service.create_default_grades(db)
    grades = db.query(SalaryGrade).all()
    return {"message": "Default grades created!", "total": len(grades)}


@router.get("/grades")
async def get_grades(db: Session = Depends(get_db)):
    return db.query(SalaryGrade).filter(SalaryGrade.is_active == True).all()


# ── Employee Salary ────────────────────────────────────────────

@router.post("/salary/set")
async def set_salary(data: SalarySet, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == data.employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    payroll_service.set_employee_salary(
        db, emp.id,
        data.basic_salary, data.house_rent, data.medical,
        data.transport, data.food, data.overtime_rate,
        data.tax_percentage, data.pf_percentage, data.grade_id
    )
    return {"message": "✅ Salary set for " + emp.full_name,
            "basic_salary": data.basic_salary}


@router.get("/salary/{employee_id}")
async def get_salary(employee_id: str, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    salary = db.query(EmployeeSalary).filter(
        EmployeeSalary.employee_id == emp.id,
        EmployeeSalary.is_active == True
    ).first()
    if not salary:
        return {"employee": emp.full_name, "salary": None,
                "message": "No salary configured"}
    return {
        "employee":       emp.full_name,
        "basic_salary":   salary.basic_salary,
        "house_rent":     salary.house_rent,
        "medical":        salary.medical,
        "transport":      salary.transport,
        "food":           salary.food,
        "total_ctc":      salary.basic_salary + salary.house_rent +
                          salary.medical + salary.transport + salary.food,
        "overtime_rate":  salary.overtime_rate,
        "tax_percentage": salary.tax_percentage,
        "pf_percentage":  salary.pf_percentage
    }


# ── Payroll Calculation ────────────────────────────────────────

@router.post("/calculate/{employee_id}")
async def calculate_payroll(
    employee_id: str,
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    record = payroll_service.calculate_payroll(db, emp.id, y, m)
    return {
        "employee_id":     employee_id,
        "employee_name":   emp.full_name,
        "year":            y,
        "month":           m,
        "present_days":    record.present_days,
        "absent_days":     record.absent_days,
        "gross_salary":    record.gross_salary,
        "total_deduction": record.total_deduction,
        "net_salary":      record.net_salary,
        "status":          record.status.value,
        "record_id":       record.id
    }


@router.post("/calculate-all")
async def calculate_all(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    results = payroll_service.calculate_all_payroll(db, y, m)
    total   = sum(r["net_salary"] for r in results)
    return {
        "year":          y,
        "month":         m,
        "total_employees": len(results),
        "total_payable": round(total, 2),
        "records":       results
    }


@router.get("/record/{employee_id}")
async def get_payroll_record(
    employee_id: str,
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    record = payroll_service.get_payroll_record(db, emp.id, y, m)
    if not record:
        raise HTTPException(status_code=404,
                            detail="Payroll not calculated yet")
    return {
        "employee_name":    emp.full_name,
        "year":             record.year,
        "month":            record.month,
        "present_days":     record.present_days,
        "absent_days":      record.absent_days,
        "late_days":        record.late_days,
        "basic_salary":     record.basic_salary,
        "house_rent":       record.house_rent,
        "medical":          record.medical,
        "transport":        record.transport,
        "food":             record.food,
        "overtime_amount":  record.overtime_amount,
        "gross_salary":     record.gross_salary,
        "absent_deduction": record.absent_deduction,
        "late_deduction":   record.late_deduction,
        "tax_deduction":    record.tax_deduction,
        "pf_deduction":     record.pf_deduction,
        "total_deduction":  record.total_deduction,
        "net_salary":       record.net_salary,
        "status":           record.status.value
    }


@router.put("/approve/{record_id}")
async def approve_payroll(
    record_id: int,
    data: PayrollApprove,
    db: Session = Depends(get_db)
):
    record = payroll_service.approve_payroll(db, record_id, data.approved_by)
    return {"message": "✅ Payroll approved!", "status": record.status.value}


@router.put("/mark-paid/{record_id}")
async def mark_paid(record_id: int, db: Session = Depends(get_db)):
    record = payroll_service.mark_paid(db, record_id)
    return {"message": "✅ Marked as paid!", "status": record.status.value}


# ── Pay Slip PDF ───────────────────────────────────────────────

@router.get("/payslip/{employee_id}")
async def download_payslip(
    employee_id: str,
    year:         int = Query(default=None),
    month:        int = Query(default=None),
    company_name: str = Query(default="Garments Factory Ltd."),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        pdf_data = payslip_service.generate_payslip(
            db, emp.id, y, m, company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    fname = "payslip_" + employee_id + "_" + str(y) + "_" + str(m).zfill(2) + ".pdf"
    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=" + fname}
    )


@router.get("/summary")
async def payroll_summary(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    records = db.query(PayrollRecord).filter(
        PayrollRecord.year  == y,
        PayrollRecord.month == m
    ).all()
    total_gross = sum(r.gross_salary  for r in records)
    total_ded   = sum(r.total_deduction for r in records)
    total_net   = sum(r.net_salary    for r in records)
    return {
        "year":          y,
        "month":         m,
        "total_records": len(records),
        "total_gross":   round(total_gross, 2),
        "total_deduction": round(total_ded, 2),
        "total_net":     round(total_net, 2),
        "draft":    sum(1 for r in records if r.status == PayrollStatus.DRAFT),
        "approved": sum(1 for r in records if r.status == PayrollStatus.APPROVED),
        "paid":     sum(1 for r in records if r.status == PayrollStatus.PAID),
    }
