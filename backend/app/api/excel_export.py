from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
import io
from app.database import get_db
from app.services.excel_service import excel_service

router = APIRouter()


@router.get("/daily")
async def export_daily(
    report_date: date = Query(default=None),
    db: Session = Depends(get_db)
):
    target = report_date or date.today()
    data   = excel_service.generate_daily_report(db, target)
    fname  = "attendance_daily_" + str(target) + ".xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=" + fname}
    )


@router.get("/monthly")
async def export_monthly(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today  = date.today()
    y      = year  or today.year
    m      = month or today.month
    data   = excel_service.generate_monthly_report(db, y, m)
    fname  = "attendance_monthly_" + str(y) + "_" + str(m).zfill(2) + ".xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=" + fname}
    )


@router.get("/salary-sheet")
async def export_salary(
    year:  int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db)
):
    today = date.today()
    y     = year  or today.year
    m     = month or today.month
    data  = excel_service.generate_salary_sheet(db, y, m)
    fname = "salary_sheet_" + str(y) + "_" + str(m).zfill(2) + ".xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=" + fname}
    )
