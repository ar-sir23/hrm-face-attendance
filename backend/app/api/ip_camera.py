from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import cv2
import io
from app.services.camera_stream_service import camera_manager
from app.config import settings

router = APIRouter()


class CameraAdd(BaseModel):
    cam_id:   str
    cam_url:  str
    cam_name: str


@router.post("/start-all")
async def start_all_cameras():
    count = camera_manager.start_all()
    return {
        "success": True,
        "message": str(count) + " camera(s) started",
        "cameras": camera_manager.get_all_status()
    }


@router.post("/stop-all")
async def stop_all_cameras():
    camera_manager.stop_all()
    return {"success": True, "message": "All cameras stopped"}


@router.post("/add")
async def add_camera(data: CameraAdd):
    cam = camera_manager.add_camera(data.cam_id, data.cam_url, data.cam_name)
    success = cam.start()
    return {
        "success": success,
        "message": data.cam_name + (" started!" if success else " failed to connect"),
        "status":  cam.get_status()
    }


@router.delete("/{cam_id}")
async def remove_camera(cam_id: str):
    cam = camera_manager.get_camera(cam_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.stop()
    del camera_manager.cameras[cam_id]
    return {"success": True, "message": cam_id + " removed"}


@router.get("/status")
async def all_camera_status():
    return {
        "total_cameras": len(camera_manager.cameras),
        "cameras": camera_manager.get_all_status()
    }


@router.get("/status/{cam_id}")
async def camera_status(cam_id: str):
    cam = camera_manager.get_camera(cam_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam.get_status()


@router.get("/snapshot/{cam_id}")
async def get_snapshot(cam_id: str):
    cam = camera_manager.get_camera(cam_id)
    if not cam or cam.latest_frame is None:
        raise HTTPException(status_code=404, detail="No frame available")
    frame = cam.draw_results(cam.latest_frame.copy())
    _, buf = cv2.imencode(".jpg", frame)
    return StreamingResponse(
        io.BytesIO(buf.tobytes()),
        media_type="image/jpeg"
    )


@router.get("/stream/{cam_id}")
async def stream_camera(cam_id: str):
    cam = camera_manager.get_camera(cam_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    def generate():
        while cam.running:
            if cam.latest_frame is None:
                continue
            frame = cam.draw_results(cam.latest_frame.copy())
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   buf.tobytes() + b"\r\n")

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
