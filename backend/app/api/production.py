from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.production_models import (
    ProductionLine, ProductionTarget, ProductionRecord,
    LineWorkerAssignment, WorkerEfficiency, LineStatus
)
from app.models.models import Employee
from app.services.production_service import production_service

router = APIRouter()


class LineCreate(BaseModel):
    name:          str
    code:          str
    floor:         Optional[str] = None
    capacity:      int = 30
    department_id: Optional[int] = None
    description:   Optional[str] = None


class TargetSet(BaseModel):
    line_id:       int
    date:          date
    product_name:  str
    target_pieces: int
    target_hours:  float = 8.0
    notes:         Optional[str] = None


class HourlyRecord(BaseModel):
    line_id:         int
    date:            date
    hour:            int
    pieces_made:     int
    defective:       int = 0
    workers_present: int = 0
    recorded_by:     Optional[str] = None


class WorkerAssign(BaseModel):
    line_id:     int
    employee_id: str
    role:        str = "WORKER"
    start_date:  date


class EfficiencyRecord(BaseModel):
    employee_id:         str
    date:                date
    actual_pieces:       int
    target_pieces:       Optional[int] = None
    quality_score:       float = 100.0
    incentive_per_piece: float = 0.5


# ── Setup ──────────────────────────────────────────────────────

@router.post("/setup")
async def setup(db: Session = Depends(get_db)):
    production_service.create_default_lines(db)
    lines = db.query(ProductionLine).count()
    return {"message": "✅ Production setup complete!",
            "total_lines": lines}


# ── Production Lines ───────────────────────────────────────────

@router.post("/lines")
async def create_line(data: LineCreate, db: Session = Depends(get_db)):
    if db.query(ProductionLine).filter(
        ProductionLine.code == data.code
    ).first():
        raise HTTPException(status_code=400,
                            detail="Line code already exists")
    line = ProductionLine(**data.dict())
    db.add(line)
    db.commit()
    db.refresh(line)
    return {"message": "✅ Line created: " + line.name, "id": line.id}


@router.get("/lines")
async def get_lines(db: Session = Depends(get_db)):
    lines = db.query(ProductionLine).filter(
        ProductionLine.is_active == True
    ).all()
    return [
        {
            "id":          l.id,
            "name":        l.name,
            "code":        l.code,
            "floor":       l.floor,
            "capacity":    l.capacity,
            "status":      l.status.value,
            "department":  l.department.name if l.department else None,
            "supervisor":  l.supervisor.full_name if l.supervisor else None
        }
        for l in lines
    ]


@router.put("/lines/{line_id}/status")
async def update_line_status(
    line_id: int,
    status:  LineStatus,
    db: Session = Depends(get_db)
):
    line = db.query(ProductionLine).filter(
        ProductionLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    line.status = status
    db.commit()
    return {"message": line.name + " status: " + status.value}


# ── Targets ────────────────────────────────────────────────────

@router.post("/targets")
async def set_target(data: TargetSet, db: Session = Depends(get_db)):
    target = production_service.set_daily_target(
        db, data.line_id, data.date,
        data.product_name, data.target_pieces,
        data.target_hours, data.notes
    )
    return {"message": "✅ Target set!", "target_id": target.id,
            "target_pieces": target.target_pieces}


@router.get("/targets")
async def get_targets(
    target_date: date = None,
    line_id:     int  = None,
    db: Session = Depends(get_db)
):
    today = target_date or date.today()
    query = db.query(ProductionTarget).filter(
        ProductionTarget.date == today)
    if line_id:
        query = query.filter(ProductionTarget.line_id == line_id)
    targets = query.all()
    return [
        {
            "id":            t.id,
            "line_name":     t.line.name,
            "line_code":     t.line.code,
            "product_name":  t.product_name,
            "target_pieces": t.target_pieces,
            "target_hours":  t.target_hours
        }
        for t in targets
    ]


# ── Production Records ─────────────────────────────────────────

@router.post("/record")
async def record_production(
    data: HourlyRecord, db: Session = Depends(get_db)):
    record = production_service.record_hourly_production(
        db, data.line_id, data.date, data.hour,
        data.pieces_made, data.defective,
        data.workers_present, data.recorded_by
    )
    return {"message": "✅ Production recorded!",
            "record_id": record.id,
            "pieces_made": record.pieces_made}


@router.get("/line/{line_id}/daily")
async def line_daily(
    line_id:     int,
    target_date: date = None,
    db: Session = Depends(get_db)
):
    today = target_date or date.today()
    return production_service.get_line_daily_summary(db, line_id, today)


@router.get("/line/{line_id}/monthly")
async def line_monthly(
    line_id: int,
    year:    int = None,
    month:   int = None,
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return production_service.get_monthly_line_report(db, line_id, y, m)


# ── Factory Dashboard ──────────────────────────────────────────

@router.get("/dashboard")
async def factory_dashboard(
    target_date: date = None,
    db: Session = Depends(get_db)
):
    today = target_date or date.today()
    return production_service.get_factory_dashboard(db, today)


# ── Worker Assignment ──────────────────────────────────────────

@router.post("/assign-worker")
async def assign_worker(data: WorkerAssign, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == data.employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    line = db.query(ProductionLine).filter(
        ProductionLine.id == data.line_id
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    # Deactivate old assignment
    old = db.query(LineWorkerAssignment).filter(
        LineWorkerAssignment.employee_id == emp.id,
        LineWorkerAssignment.is_active   == True
    ).first()
    if old:
        old.is_active = False

    assignment = LineWorkerAssignment(
        line_id=data.line_id, employee_id=emp.id,
        role=data.role, start_date=data.start_date, is_active=True
    )
    db.add(assignment)
    db.commit()
    return {"message": "✅ " + emp.full_name + " assigned to " + line.name,
            "role": data.role}


@router.get("/line/{line_id}/workers")
async def line_workers(line_id: int, db: Session = Depends(get_db)):
    assignments = db.query(LineWorkerAssignment).filter(
        LineWorkerAssignment.line_id   == line_id,
        LineWorkerAssignment.is_active == True
    ).all()
    return [
        {
            "employee_id":   a.employee.employee_id,
            "employee_name": a.employee.full_name,
            "role":          a.role,
            "start_date":    a.start_date.isoformat()
        }
        for a in assignments
    ]


# ── Worker Efficiency ──────────────────────────────────────────

@router.post("/efficiency")
async def record_efficiency(
    data: EfficiencyRecord, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(
        Employee.employee_id == data.employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    record = production_service.calculate_worker_efficiency(
        db, emp.id, data.date, data.actual_pieces,
        data.target_pieces, data.quality_score,
        data.incentive_per_piece
    )
    return {
        "employee_name":   emp.full_name,
        "date":            data.date.isoformat(),
        "actual_pieces":   record.actual_pieces,
        "target_pieces":   record.target_pieces,
        "efficiency_pct":  record.efficiency_pct,
        "quality_score":   record.quality_score,
        "incentive_earned":record.incentive_earned
    }


@router.get("/top-performers")
async def top_performers(
    year:  int = None,
    month: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return {
        "year":     y,
        "month":    m,
        "top_performers": production_service.get_top_performers(db, y, m, limit)
    }


@router.get("/efficiency/{employee_id}")
async def worker_efficiency_history(
    employee_id: str,
    year:        int = None,
    month:       int = None,
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    today  = date.today()
    y      = year  or today.year
    m      = month or today.month
    import calendar as cal
    first  = date(y, m, 1)
    last   = date(y, m, cal.monthrange(y, m)[1])
    records = db.query(WorkerEfficiency).filter(
        WorkerEfficiency.employee_id == emp.id,
        WorkerEfficiency.date >= first,
        WorkerEfficiency.date <= last
    ).order_by(WorkerEfficiency.date.desc()).all()
    return {
        "employee_name": emp.full_name,
        "records": [
            {
                "date":            r.date.isoformat(),
                "actual_pieces":   r.actual_pieces,
                "target_pieces":   r.target_pieces,
                "efficiency_pct":  r.efficiency_pct,
                "quality_score":   r.quality_score,
                "incentive_earned":r.incentive_earned
            }
            for r in records
        ]
    }
