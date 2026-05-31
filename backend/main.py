from app.api import compliance
from app.api import production
from app.api import liveness
from app.api import leaves
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, asyncio, json, base64, logging
from datetime import datetime
from app.database import engine, Base, SessionLocal
from app.services.face_service import get_face_service
from app.services.attendance_service import AttendanceService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="HRM Face Attendance", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

face_service       = get_face_service()
attendance_service = AttendanceService()

@app.on_event("startup")
async def startup():
    # ── Core database ──────────────────────────────
    Base.metadata.create_all(bind=engine)

    # ── Shift tables ───────────────────────────────
    from app.models import shift_models
    shift_models.Base.metadata.create_all(bind=engine)

    # ── Payroll tables ─────────────────────────────
    from app.models import payroll_models
    payroll_models.Base.metadata.create_all(bind=engine)

    logger.info("✅ Database ready")
    logger.info("🚀 HRM Face Attendance System started!")

    from app.models import leave_models
    leave_models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        from app.services.leave_service import leave_service

        leave_service.create_default_policies(db)
        leave_service.create_default_holidays(db)
        leave_service.initialize_all_employees(db)

    finally:
        db.close()

        from app.models import production_models
        production_models.Base.metadata.create_all(bind=engine)

        from app.services.production_service import production_service
        production_service.create_default_lines(db)

    # ── Background tasks ───────────────────────────
    from app.services.alert_scheduler import alert_scheduler
    asyncio.create_task(alert_scheduler.run())
    logger.info("📧 Email alert scheduler started!")

    from app.services.camera_stream_service import camera_manager
    started = camera_manager.start_all()
    logger.info("📷 " + str(started) + " IP camera(s) started!")

    # ── Default data ───────────────────────────────
    db = SessionLocal()
    try:
        from app.services.shift_service import shift_service
        shift_service.create_default_shifts(db)

        from app.services.payroll_service import payroll_service
        payroll_service.create_default_grades(db)
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown():
    from app.services.camera_stream_service import camera_manager
    camera_manager.stop_all()
    logger.info("📷 All cameras stopped")

# ── API Routes ─────────────────────────────────────
from app.api import employees, attendance, auth, camera
from app.api import email_alerts, ip_camera, excel_export, shifts, payroll

app.include_router(auth.router,         prefix="/api/auth",         tags=["Auth"])
app.include_router(employees.router,    prefix="/api/employees",    tags=["Employees"])
app.include_router(attendance.router,   prefix="/api/attendance",   tags=["Attendance"])
app.include_router(camera.router,       prefix="/api/camera",       tags=["Camera"])
app.include_router(email_alerts.router, prefix="/api/alerts",       tags=["Email Alerts"])
app.include_router(ip_camera.router,    prefix="/api/ip-camera",    tags=["IP Camera"])
app.include_router(excel_export.router, prefix="/api/export",       tags=["Excel Export"])
app.include_router(shifts.router,       prefix="/api/shifts",       tags=["Shifts"])
app.include_router(payroll.router,      prefix="/api/payroll",      tags=["Payroll"])
app.include_router(leaves.router, prefix="/api/leaves", tags=["Leave Management"])
app.include_router(liveness.router, prefix="/api/liveness", tags=["Anti-Spoofing"])
app.include_router(production.router, prefix="/api/production", tags=["Production"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])

# ── WebSocket ──────────────────────────────────────
class WSManager:
    def __init__(self):
        self.connections = []
    async def connect(self, ws):
        await ws.accept()
        self.connections.append(ws)
    def disconnect(self, ws):
        if ws in self.connections:
            self.connections.remove(ws)

manager = WSManager()

@app.websocket("/ws/camera")
async def websocket_camera(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data    = await websocket.receive_text()
            payload = json.loads(data)
            if payload.get("type") == "frame":
                img = payload["image"]
                if "," in img:
                    img = img.split(",")[1]
                result = await face_service.process_frame_async(base64.b64decode(img))
                await websocket.send_json({
                    "type":      "result",
                    "timestamp": datetime.now().isoformat(),
                    "data":      result
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "✅ HRM Face Attendance running!", "docs": "/api/docs"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
