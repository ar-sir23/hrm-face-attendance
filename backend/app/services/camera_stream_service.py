import cv2
import asyncio
import logging
import threading
import numpy as np
from datetime import datetime, date
from app.config import settings
from app.services.face_service import get_face_service
from app.database import SessionLocal
from app.services.attendance_service import AttendanceService

logger = logging.getLogger(__name__)
face_service = get_face_service()
attendance_service = AttendanceService()


class IPCameraStream:
    """
    Single IP camera stream processor.
    Reads frames, detects faces, records attendance automatically.
    """

    def __init__(self, cam_url, cam_name="Camera", cam_id="CAM_1"):
        self.cam_url  = cam_url
        self.cam_name = cam_name
        self.cam_id   = cam_id
        self.running  = False
        self.cap      = None
        self.frame_count      = 0
        self.last_recognition = {}
        self.total_punches    = 0
        self.thread   = None
        self.latest_frame     = None
        self.latest_results   = []

    def connect(self):
        try:
            url = int(self.cam_url) if self.cam_url.isdigit() else self.cam_url
            self.cap = cv2.VideoCapture(url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self.cap.isOpened():
                logger.info("Camera connected: " + self.cam_name + " (" + str(self.cam_url) + ")")
                return True
            else:
                logger.error("Cannot connect to camera: " + self.cam_name)
                return False
        except Exception as e:
            logger.error("Camera connect error: " + str(e))
            return False

    def process_frame(self, frame):
        try:
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            _, buf = cv2.imencode(".jpg", small)
            image_bytes = buf.tobytes()
            result = face_service.recognize_face(image_bytes)
            self.latest_results = result.get("faces", [])

            for face in result.get("faces", []):
                if not face.get("recognized"):
                    continue
                emp_id     = face["employee_id"]
                confidence = face["confidence"]
                if confidence < settings.CAM_MIN_CONFIDENCE:
                    continue
                now = datetime.now()
                last = self.last_recognition.get(emp_id)
                if last and (now - last).seconds < settings.DUPLICATE_PUNCH_INTERVAL:
                    continue
                self.last_recognition[emp_id] = now
                db = SessionLocal()
                try:
                    img_data = None
                    if settings.CAM_SAVE_CAPTURES:
                        _, full_buf = cv2.imencode(".jpg", frame)
                        img_data = full_buf.tobytes()
                    punch_result = attendance_service.record_attendance(
                        db=db,
                        employee_id=emp_id,
                        confidence=confidence,
                        image_data=img_data,
                        camera_id=self.cam_id,
                        location=self.cam_name,
                        method="FACE_AUTO"
                    )
                    if punch_result.get("success"):
                        self.total_punches += 1
                        logger.info(
                            "AUTO PUNCH: " + face["employee_name"] +
                            " | " + self.cam_name +
                            " | " + str(round(confidence, 1)) + "%" +
                            " | " + punch_result.get("punch_type", "")
                        )
                finally:
                    db.close()

        except Exception as e:
            logger.error("Frame processing error: " + str(e))

    def draw_results(self, frame):
        for face in self.latest_results:
            loc = face.get("face_location", {})
            if not loc:
                continue
            top    = loc.get("top", 0)    * 2
            right  = loc.get("right", 0)  * 2
            bottom = loc.get("bottom", 0) * 2
            left   = loc.get("left", 0)   * 2
            if face.get("recognized"):
                color = (0, 200, 0)
                label = face["employee_name"] + " " + str(round(face["confidence"], 0)) + "%"
            else:
                color = (0, 0, 200)
                label = "Unknown"
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 4, bottom - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, self.cam_name + " | " + ts,
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 212, 170), 2)
        cv2.putText(frame, "Total Punches: " + str(self.total_punches),
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame

    def _run_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Frame read failed, reconnecting: " + self.cam_name)
                self.cap.release()
                if not self.connect():
                    import time
                    time.sleep(5)
                continue
            self.latest_frame = frame.copy()
            self.frame_count += 1
            if self.frame_count % settings.CAM_PROCESS_EVERY_N_FRAMES == 0:
                self.process_frame(frame)

    def start(self):
        if not self.connect():
            return False
        self.running = True
        self.thread  = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Camera stream started: " + self.cam_name)
        return True

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        logger.info("Camera stream stopped: " + self.cam_name)

    def get_status(self):
        return {
            "cam_id":        self.cam_id,
            "cam_name":      self.cam_name,
            "cam_url":       str(self.cam_url),
            "running":       self.running,
            "frame_count":   self.frame_count,
            "total_punches": self.total_punches,
            "connected":     self.cap.isOpened() if self.cap else False
        }


class CameraStreamManager:
    """Manages multiple IP cameras."""

    def __init__(self):
        self.cameras = {}

    def add_camera(self, cam_id, cam_url, cam_name):
        if cam_id in self.cameras:
            self.cameras[cam_id].stop()
        cam = IPCameraStream(cam_url, cam_name, cam_id)
        self.cameras[cam_id] = cam
        return cam

    def start_all(self):
        started = 0
        if settings.CAM_1_URL and settings.CAM_1_URL.strip():
            cam = self.add_camera("CAM_1", settings.CAM_1_URL, settings.CAM_1_NAME)
            if cam.start():
                started += 1
        if settings.CAM_2_URL and settings.CAM_2_URL.strip():
            cam = self.add_camera("CAM_2", settings.CAM_2_URL, settings.CAM_2_NAME)
            if cam.start():
                started += 1
        if started == 0:
            logger.info("No IP cameras configured. Add via API when ready.")
        else:
            logger.info(str(started) + " camera(s) started")
        return started


    def stop_all(self):
        for cam in self.cameras.values():
            cam.stop()
        self.cameras.clear()

    def get_all_status(self):
        return [cam.get_status() for cam in self.cameras.values()]

    def get_camera(self, cam_id):
        return self.cameras.get(cam_id)


camera_manager = CameraStreamManager()
