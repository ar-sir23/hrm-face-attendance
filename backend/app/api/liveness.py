from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import base64
import uuid
from app.database import get_db
from app.services.liveness_service import liveness_service
from app.services.face_service import get_face_service
from app.services.attendance_service import AttendanceService

router = APIRouter()
face_service       = get_face_service()
attendance_service = AttendanceService()


@router.post("/check-frame")
async def check_frame(
    file:       UploadFile = File(...),
    session_id: str        = Form(...)
):
    """
    Check a single frame for liveness.
    Call this repeatedly with webcam frames.
    """
    image_data = await file.read()
    result     = liveness_service.process_frame(session_id, image_data)
    return result


@router.post("/check-frame-base64")
async def check_frame_base64(
    image_base64: str,
    session_id:   str
):
    """Check frame from base64 (WebSocket / webcam)"""
    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        image_data = base64.b64decode(image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image")
    result = liveness_service.process_frame(session_id, image_data)
    return result


@router.post("/verify-and-punch")
async def verify_and_punch(
    file:            UploadFile = File(...),
    session_id:      str        = Form(...),
    camera_id:       Optional[str] = Form(None),
    location:        Optional[str] = Form("Main Gate"),
    required_blinks: int           = Form(1),
    db: Session = Depends(get_db)
):
    """
    Verify liveness then record attendance if real person detected.
    This is the main anti-spoofing attendance endpoint.
    """
    image_data = await file.read()

    # Step 1: Liveness check
    liveness = liveness_service.verify_liveness(
        session_id, image_data, required_blinks)

    if not liveness["verified"]:
        return {
            "success":   False,
            "step":      "liveness",
            "message":   "❌ " + liveness["reason"],
            "blinks":    liveness["blinks"],
            "confidence":liveness["confidence"]
        }

    # Step 2: Face recognition
    recognition = face_service.recognize_face(image_data)

    if not recognition["recognized"]:
        return {
            "success":   False,
            "step":      "recognition",
            "message":   "❌ Face not recognized. Please try again.",
            "liveness":  liveness
        }

    # Step 3: Record attendance
    records = []
    for face in recognition["faces"]:
        if face["recognized"]:
            record = attendance_service.record_attendance(
                db=db,
                employee_id=face["employee_id"],
                confidence=face["confidence"],
                image_data=image_data,
                camera_id=camera_id,
                location=location,
                method="FACE_ANTISPOOF"
            )
            records.append(record)

    return {
        "success":          True,
        "liveness_verified":True,
        "liveness_score":   liveness["confidence"],
        "blinks_detected":  liveness["blinks"],
        "records":          records,
        "message":          "✅ Liveness verified and attendance recorded!"
    }


@router.post("/new-session")
async def new_session():
    """Create a new liveness session ID"""
    session_id = str(uuid.uuid4())[:8]
    return {"session_id": session_id}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current session liveness status"""
    return liveness_service.get_session_status(session_id)


@router.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Reset/clear a liveness session"""
    liveness_service.reset_session(session_id)
    return {"message": "Session reset: " + session_id}


@router.post("/test-image")
async def test_image(file: UploadFile = File(...)):
    """
    Test an image for liveness indicators.
    Useful for debugging and tuning.
    """
    image_data  = await file.read()
    session_id  = "test_" + str(uuid.uuid4())[:4]
    result      = liveness_service.process_frame(session_id, image_data)
    liveness_service.reset_session(session_id)
    return {
        "face_detected":  result["face_detected"],
        "liveness_score": result["confidence"],
        "ear_value":      result.get("ear", 0),
        "checks":         result["checks"],
        "instruction":    result["instruction"],
        "would_pass":     result["confidence"] >= 65
    }
