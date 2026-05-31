from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.leave_models import (
    LeaveApplication, LeaveBalance, LeavePolicy,
    LeaveType, LeaveStatus, Holiday
)
from app.models.models import Employee
from app.services.leave_service import leave_service

router = APIRouter()


class LeaveApply(BaseModel):
    employee_id:    str
    leave_type:     LeaveType
    start_date:     date
    end_date:       date
    reason:         str
    contact_number: Optional[str] = None
    handover_to:    Optional[str] = None


class LeaveAction(BaseModel):
    action_by: str
    reason:    Optional[str] = None


class HolidayCreate(BaseModel):
    name:        str
    date:        date
    description: Optional[str] = None
    is_optional: bool = False


# ── Setup ──────────────────────────────────────────────────────

@router.post("/setup")
async def setup_leave(db: Session = Depends(get_db)):
    leave_service.create_default_policies(db)
    leave_service.create_default_holidays(db)
    leave_service.initialize_all_employees(db)
    return {"message": "✅ Leave management setup complete!"}


@router.post("/initialize-balances")
async def init_balances(year: int = None, db: Session = Depends(get_db)):
    y = year or date.today().year
    leave_service.initialize_all_employees(db, y)
    return {"message": "✅ Leave balances initialized for " + str(y)}


# ── Policies ───────────────────────────────────────────────────

@router.get("/policies")
async def get_policies(db: Session = Depends(get_db)):
    return db.query(LeavePolicy).filter(LeavePolicy.is_active == True).all()


# ── Holidays ───────────────────────────────────────────────────

@router.get("/holidays")
async def get_holidays(
    year: int = None,
    db: Session = Depends(get_db)
):
    y = year or date.today().year
    holidays = db.query(Holiday).filter(
        Holiday.date >= date(y, 1, 1),
        Holiday.date <= date(y, 12, 31)
    ).order_by(Holiday.date).all()
    return [
        {
            "id":          h.id,
            "name":        h.name,
            "date":        h.date.isoformat(),
            "description": h.description,
            "is_optional": h.is_optional
        }
        for h in holidays
    ]


@router.post("/holidays")
async def add_holiday(data: HolidayCreate, db: Session = Depends(get_db)):
    holiday = Holiday(**data.dict())
    db.add(holiday)
    db.commit()
    return {"message": "✅ Holiday added: " + data.name}


# ── Leave Balance ──────────────────────────────────────────────

@router.get("/balance/{employee_id}")
async def get_balance(
    employee_id: str,
    year: int = None,
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    y       = year or date.today().year
    balance = leave_service.get_employee_balance(db, emp.id, y)
    return {
        "employee_id":   employee_id,
        "employee_name": emp.full_name,
        "year":          y,
        "balances":      balance
    }


# ── Leave Application ──────────────────────────────────────────

@router.post("/apply")
async def apply_leave(data: LeaveApply, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == data.employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    result = leave_service.apply_leave(
        db, emp.id, data.leave_type,
        data.start_date, data.end_date,
        data.reason, data.contact_number, data.handover_to
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/applications/pending")
async def pending_applications(db: Session = Depends(get_db)):
    apps = leave_service.get_pending_applications(db)
    return {"total": len(apps), "applications": apps}


@router.get("/applications/{employee_id}")
async def employee_applications(
    employee_id: str,
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    apps = leave_service.get_employee_applications(db, emp.id)
    return {"employee_name": emp.full_name, "applications": apps}


@router.put("/approve/{application_id}")
async def approve(
    application_id: int,
    data: LeaveAction,
    db: Session = Depends(get_db)
):
    result = leave_service.approve_leave(db, application_id, data.action_by)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/reject/{application_id}")
async def reject(
    application_id: int,
    data: LeaveAction,
    db: Session = Depends(get_db)
):
    result = leave_service.reject_leave(
        db, application_id, data.action_by, data.reason or "")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/cancel/{application_id}")
async def cancel(
    application_id: int,
    employee_id: str,
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    result = leave_service.cancel_leave(db, application_id, emp.id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/summary")
async def leave_summary(db: Session = Depends(get_db)):
    pending  = db.query(LeaveApplication).filter(
        LeaveApplication.status == LeaveStatus.PENDING).count()
    approved = db.query(LeaveApplication).filter(
        LeaveApplication.status == LeaveStatus.APPROVED,
        LeaveApplication.start_date <= date.today(),
        LeaveApplication.end_date   >= date.today()
    ).count()
    total    = db.query(LeaveApplication).count()
    return {
        "pending_applications":  pending,
        "employees_on_leave":    approved,
        "total_applications":    total
    }
