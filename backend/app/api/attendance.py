from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, date
from app.database import get_db
from app.models.models import Employee, AttendanceLog, AttendanceSummary, AttendanceType, AttendanceStatus
from app.services.face_service import get_face_service
from app.services.attendance_service import AttendanceService

router = APIRouter()
face_service = get_face_service()
attendance_service = AttendanceService()

class ManualPunch(BaseModel):
    employee_id: str
    punch_type: AttendanceType
    punch_time: Optional[datetime] = None

@router.post("/face-punch")
async def face_punch(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    image_data = await file.read()
    result = face_service.recognize_face(image_data)
    if not result["recognized"]:
        return {"success": False, "message": "কোনো পরিচিত কর্মীর মুখ শনাক্ত হয়নি"}
    records = []
    for face in result["faces"]:
        if face["recognized"]:
            r = attendance_service.record_attendance(
                db, face["employee_id"], face["confidence"], image_data, camera_id, location
            )
            records.append(r)
    return {"success": True, "records": records}

@router.post("/manual-punch")
async def manual_punch(data: ManualPunch, db: Session = Depends(get_db)):
    punch_time = data.punch_time or datetime.now()
    emp = db.query(Employee).filter(Employee.employee_id == data.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="কর্মী পাওয়া যায়নি")
    log = AttendanceLog(
        employee_id=emp.id,
        punch_time=punch_time,
        punch_type=data.punch_type,
        recognition_method="MANUAL"
    )
    db.add(log)
    attendance_service._update_summary(db, emp.id, punch_time.date(), data.punch_type, punch_time)
    db.commit()
    action = "প্রবেশ" if data.punch_type == AttendanceType.IN else "বাহির"
    return {"success": True, "message": f"✅ {emp.full_name} — {action} রেকর্ড হয়েছে"}

@router.get("/today")
async def today_summary(db: Session = Depends(get_db)):
    return attendance_service.get_today_report(db)

@router.get("/today/details")
async def today_details(db: Session = Depends(get_db)):
    today = date.today()
    summaries = db.query(AttendanceSummary).filter(
        AttendanceSummary.date == today
    ).join(Employee).all()
    return {
        "date": today.isoformat(),
        "total": len(summaries),
        "records": [
            {
                "employee_id": s.employee.employee_id,
                "employee_name": s.employee.full_name,
                "status": s.status.value,
                "first_in": s.first_in.strftime("%H:%M:%S") if s.first_in else None,
                "last_out": s.last_out.strftime("%H:%M:%S") if s.last_out else None,
                "work_hours": s.work_hours,
                "is_late": s.is_late
            }
            for s in summaries
        ]
    }

@router.get("/logs/today")
async def today_logs(employee_id: Optional[str] = None, db: Session = Depends(get_db)):
    today = date.today()
    q = db.query(AttendanceLog).join(Employee).filter(
        func.date(AttendanceLog.punch_time) == today
    )
    if employee_id:
        q = q.filter(Employee.employee_id == employee_id)
    logs = q.order_by(AttendanceLog.punch_time.desc()).all()
    return {
        "total": len(logs),
        "logs": [
            {
                "employee_name": l.employee.full_name,
                "punch_type": l.punch_type.value,
                "punch_time": l.punch_time.strftime("%H:%M:%S"),
                "confidence": l.confidence_score,
                "method": l.recognition_method
            }
            for l in logs
        ]
    }

@router.get("/report/late-today")
async def late_today(db: Session = Depends(get_db)):
    today = date.today()
    late = db.query(AttendanceSummary).filter(
        AttendanceSummary.date == today,
        AttendanceSummary.is_late == True
    ).join(Employee).all()
    return {
        "date": today.isoformat(),
        "total_late": len(late),
        "employees": [
            {
                "employee_name": s.employee.full_name,
                "arrival_time": s.first_in.strftime("%H:%M") if s.first_in else None,
                "late_minutes": s.late_minutes
            }
            for s in late
        ]
    }
