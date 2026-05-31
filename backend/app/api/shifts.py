from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.database import get_db
from app.models.shift_models import Shift, EmployeeShift, OvertimeRecord, ShiftType
from app.models.models import Employee
from app.services.shift_service import shift_service

router = APIRouter()


class ShiftCreate(BaseModel):
    name:                  str
    shift_type:            ShiftType = ShiftType.GENERAL
    start_time:            str
    end_time:              str
    late_after:            str
    grace_minutes:         int = 15
    overtime_after_hours:  int = 8
    is_night_shift:        bool = False


class ShiftAssign(BaseModel):
    employee_id: str
    shift_id:    int
    start_date:  date
    end_date:    Optional[date] = None


class OvertimeApprove(BaseModel):
    approved:    bool
    approved_by: str
    note:        Optional[str] = None


# ── Shift CRUD ─────────────────────────────────────────────────

@router.post("/create-defaults")
async def create_defaults(db: Session = Depends(get_db)):
    shift_service.create_default_shifts(db)
    shifts = db.query(Shift).all()
    return {"message": "Default shifts created!", "total": len(shifts)}


@router.post("/")
async def create_shift(data: ShiftCreate, db: Session = Depends(get_db)):
    shift = Shift(**data.dict())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return {"message": "Shift created!", "shift_id": shift.id, "name": shift.name}


@router.get("/")
async def get_shifts(db: Session = Depends(get_db)):
    shifts = db.query(Shift).filter(Shift.is_active == True).all()
    return [
        {
            "id":                    s.id,
            "name":                  s.name,
            "shift_type":            s.shift_type.value,
            "start_time":            s.start_time,
            "end_time":              s.end_time,
            "late_after":            s.late_after,
            "grace_minutes":         s.grace_minutes,
            "overtime_after_hours":  s.overtime_after_hours,
            "is_night_shift":        s.is_night_shift
        }
        for s in shifts
    ]


@router.delete("/{shift_id}")
async def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    shift.is_active = False
    db.commit()
    return {"message": shift.name + " deactivated"}


# ── Employee Shift Assignment ───────────────────────────────────

@router.post("/assign")
async def assign_shift(data: ShiftAssign, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == data.employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    shift = db.query(Shift).filter(Shift.id == data.shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    assignment = shift_service.assign_shift(
        db, emp.id, data.shift_id, data.start_date, data.end_date)
    return {
        "message":      emp.full_name + " assigned to " + shift.name,
        "employee":     emp.full_name,
        "shift":        shift.name,
        "start_date":   data.start_date.isoformat(),
        "end_date":     data.end_date.isoformat() if data.end_date else None
    }


@router.get("/employee/{employee_id}")
async def get_employee_shift(employee_id: str, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    shift = shift_service.get_employee_shift(db, emp.id)
    if not shift:
        return {"employee": emp.full_name, "shift": None,
                "message": "No shift assigned"}
    return {
        "employee":   emp.full_name,
        "shift_id":   shift.id,
        "shift_name": shift.name,
        "shift_type": shift.shift_type.value,
        "start_time": shift.start_time,
        "end_time":   shift.end_time
    }


@router.get("/summary")
async def shift_summary(
    report_date: date = None,
    db: Session = Depends(get_db)
):
    target = report_date or date.today()
    return shift_service.get_shift_summary(db, target)


# ── Overtime ───────────────────────────────────────────────────

@router.post("/overtime/calculate/{employee_id}")
async def calc_overtime(
    employee_id: str,
    target_date: date = None,
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    target = target_date or date.today()
    record = shift_service.calculate_overtime(db, emp.id, target)
    if not record:
        return {"message": "No attendance data found for this date"}
    return {
        "employee":       emp.full_name,
        "date":           target.isoformat(),
        "actual_hours":   record.actual_hours,
        "regular_hours":  record.regular_hours,
        "overtime_hours": record.overtime_hours,
        "approved":       record.approved
    }


@router.get("/overtime/monthly")
async def monthly_overtime(
    year:  int = None,
    month: int = None,
    db: Session = Depends(get_db)
):
    from datetime import date as d
    today = d.today()
    y = year  or today.year
    m = month or today.month
    return {
        "year":    y,
        "month":   m,
        "records": shift_service.get_monthly_overtime(db, y, m)
    }


@router.put("/overtime/{record_id}/approve")
async def approve_overtime(
    record_id: int,
    data: OvertimeApprove,
    db: Session = Depends(get_db)
):
    record = db.query(OvertimeRecord).filter(
        OvertimeRecord.id == record_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    record.approved    = data.approved
    record.approved_by = data.approved_by
    record.note        = data.note
    db.commit()
    return {
        "message":  "Overtime " + ("approved" if data.approved else "rejected"),
        "record_id": record_id,
        "approved":  data.approved
    }
