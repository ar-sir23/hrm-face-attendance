from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import base64
from app.database import get_db
from app.services.face_service import get_face_service
from app.services.attendance_service import AttendanceService

router = APIRouter()
face_service = get_face_service()
attendance_service = AttendanceService()

@router.post("/recognize")
async def recognize(
    file: UploadFile = File(...),
    auto_record: bool = Form(False),
    camera_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    image_data = await file.read()
    result = face_service.recognize_face(image_data)
    if auto_record and result["recognized"]:
        records = []
        for face in result["faces"]:
            if face["recognized"]:
                r = attendance_service.record_attendance(
                    db, face["employee_id"], face["confidence"], image_data, camera_id
                )
                records.append(r)
        result["attendance_records"] = records
    return result

@router.get("/status")
async def cam_status():
    return {
        "active": True,
        "registered_employees": face_service.get_registered_count(),
        "model": "hog",
        "status": "✅ সক্রিয়"
    }
