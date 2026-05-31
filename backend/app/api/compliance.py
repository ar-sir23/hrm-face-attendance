from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import io
import json
from app.database import get_db
from app.services.compliance_service import compliance_service

router = APIRouter()


@router.get("/full-report")
async def full_compliance_report(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    """Complete labour law compliance report"""
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return compliance_service.generate_full_compliance_report(db, y, m)


@router.get("/overtime")
async def overtime_compliance(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return compliance_service.check_overtime_compliance(db, y, m)


@router.get("/minimum-wage")
async def minimum_wage_compliance(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return compliance_service.check_minimum_wage_compliance(db, y, m)


@router.get("/weekly-holiday")
async def weekly_holiday_compliance(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return compliance_service.check_weekly_holiday_compliance(db, y, m)


@router.get("/leave-entitlement")
async def leave_compliance(
    year: int = Query(default=None),
    db: Session = Depends(get_db)
):
    y = year or date.today().year
    return compliance_service.check_leave_compliance(db, y)


@router.get("/bgmea-report")
async def bgmea_report(
    year:         int = Query(default=None),
    month:        int = Query(default=None),
    factory_name: str = Query(default="Garments Factory Ltd."),
    factory_code: str = Query(default="BGMEA-0000"),
    db: Session = Depends(get_db)
):
    """BGMEA format workforce compliance report"""
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return compliance_service.generate_bgmea_report(
        db, y, m, factory_name, factory_code)


@router.get("/audit-trail")
async def audit_trail(
    start_date:  date = Query(default=None),
    end_date:    date = Query(default=None),
    employee_id: Optional[str] = Query(default=None),
    action_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Complete audit trail of attendance actions"""
    today = date.today()
    s = start_date or date(today.year, today.month, 1)
    e = end_date   or today
    logs = compliance_service.get_audit_trail(db, s, e, employee_id, action_type)
    return {
        "start_date":   s.isoformat(),
        "end_date":     e.isoformat(),
        "total_records":len(logs),
        "logs":         logs
    }


@router.get("/suspicious")
async def suspicious_activities(
    target_date: date = Query(default=None),
    db: Session = Depends(get_db)
):
    """Detect suspicious attendance patterns"""
    today = target_date or date.today()
    items = compliance_service.get_suspicious_activities(db, today)
    return {
        "date":     today.isoformat(),
        "total":    len(items),
        "items":    items,
        "status":   "✅ No suspicious activity" if not items
                    else "⚠️ " + str(len(items)) + " items need review"
    }


@router.get("/export-json")
async def export_compliance_json(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    """Export full compliance report as JSON file"""
    today = date.today()
    y = year  or today.year
    m = month or today.month
    report  = compliance_service.generate_full_compliance_report(db, y, m)
    bgmea   = compliance_service.generate_bgmea_report(db, y, m)
    full    = {"compliance_report": report, "bgmea_report": bgmea}
    content = json.dumps(full, indent=2, ensure_ascii=False)
    fname   = "compliance_" + str(y) + "_" + str(m).zfill(2) + ".json"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=" + fname}
    )
