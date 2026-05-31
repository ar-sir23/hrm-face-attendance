import cv2
import numpy as np
import face_recognition
import logging
from scipy.spatial import distance
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LivenessService:
    """
    Anti-spoofing service using:
    1. Eye blink detection (EAR - Eye Aspect Ratio)
    2. Head movement detection
    3. Texture analysis (LBP - Local Binary Pattern)
    4. Face size consistency check
    """

    # Eye landmark indices (dlib 68-point model)
    LEFT_EYE  = list(range(36, 42))
    RIGHT_EYE = list(range(42, 48))

    # Thresholds
    EAR_THRESHOLD      = 0.25   # below = eye closed
    EAR_CONSEC_FRAMES  = 2      # frames eye must be closed
    MIN_FACE_SIZE      = 80     # minimum face size in pixels
    TEXTURE_THRESHOLD  = 15.0   # LBP texture variance threshold

    def __init__(self):
        self.blink_counter    = {}   # per session blink count
        self.ear_history      = {}   # per session EAR history
        self.frame_history    = {}   # per session frame count
        self.head_positions   = {}   # per session head position history
        logger.info("Liveness detection service started")

    def eye_aspect_ratio(self, eye_points) -> float:
        """Calculate Eye Aspect Ratio (EAR)"""
        A = distance.euclidean(eye_points[1], eye_points[5])
        B = distance.euclidean(eye_points[2], eye_points[4])
        C = distance.euclidean(eye_points[0], eye_points[3])
        return (A + B) / (2.0 * C)

    def get_face_landmarks(self, image_data: bytes):
        """Get 68 face landmarks from image"""
        try:
            nparr  = np.frombuffer(image_data, np.uint8)
            image  = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb    = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            landmarks = face_recognition.face_landmarks(rgb)
            if not landmarks:
                return None, None, image
            return landmarks[0], rgb, image
        except Exception as e:
            logger.error("Landmark error: " + str(e))
            return None, None, None

    def calculate_ear(self, landmarks: dict) -> float:
        """Calculate EAR from face landmarks"""
        try:
            left_eye  = [(p[0], p[1]) for p in landmarks.get("left_eye",  [])]
            right_eye = [(p[0], p[1]) for p in landmarks.get("right_eye", [])]
            if len(left_eye) < 6 or len(right_eye) < 6:
                return 0.3
            left_ear  = self.eye_aspect_ratio(left_eye)
            right_ear = self.eye_aspect_ratio(right_eye)
            return (left_ear + right_ear) / 2.0
        except Exception as e:
            logger.error("EAR error: " + str(e))
            return 0.3

    def get_nose_position(self, landmarks: dict) -> Optional[tuple]:
        """Get nose tip position for head movement tracking"""
        nose = landmarks.get("nose_tip", [])
        if nose:
            return nose[0]
        return None

    def check_texture(self, image: np.ndarray,
                       face_location: tuple) -> float:
        """
        LBP texture analysis — real faces have more texture variance
        than printed photos
        """
        try:
            top, right, bottom, left = face_location
            face_roi = image[top:bottom, left:right]
            if face_roi.size == 0:
                return 20.0
            gray     = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            gray     = cv2.resize(gray, (64, 64))
            lbp      = self._compute_lbp(gray)
            variance = float(np.var(lbp))
            return variance
        except Exception as e:
            logger.error("Texture error: " + str(e))
            return 20.0

    def _compute_lbp(self, gray: np.ndarray) -> np.ndarray:
        """Simple LBP computation"""
        rows, cols = gray.shape
        lbp        = np.zeros_like(gray)
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center    = gray[i, j]
                code      = 0
                neighbors = [
                    gray[i-1, j-1], gray[i-1, j], gray[i-1, j+1],
                    gray[i,   j+1], gray[i+1, j+1], gray[i+1, j],
                    gray[i+1, j-1], gray[i,   j-1]
                ]
                for bit, neighbor in enumerate(neighbors):
                    if neighbor >= center:
                        code |= (1 << bit)
                lbp[i, j] = code
        return lbp

    def check_face_size(self, face_location: tuple,
                         image_shape: tuple) -> bool:
        """Check if face is large enough (not a photo from distance)"""
        top, right, bottom, left = face_location
        face_height = bottom - top
        face_width  = right  - left
        return (face_height >= self.MIN_FACE_SIZE and
                face_width  >= self.MIN_FACE_SIZE)

    def process_frame(self, session_id: str,
                       image_data: bytes) -> dict:
        """
        Process a single frame for liveness detection.
        Call this for each webcam frame.
        Returns liveness status and instructions.
        """
        # Initialize session
        if session_id not in self.blink_counter:
            self.blink_counter[session_id]  = 0
            self.ear_history[session_id]    = []
            self.frame_history[session_id]  = 0
            self.head_positions[session_id] = []

        self.frame_history[session_id] += 1
        frame_num = self.frame_history[session_id]

        # Get landmarks
        landmarks, rgb, image = self.get_face_landmarks(image_data)

        if landmarks is None or image is None:
            return {
                "live":          False,
                "face_detected": False,
                "blinks":        self.blink_counter[session_id],
                "frame":         frame_num,
                "instruction":   "👤 Please look at the camera",
                "confidence":    0,
                "checks":        {}
            }

        # Face location
        nparr          = np.frombuffer(image_data, np.uint8)
        img            = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img        = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_img)

        checks = {
            "face_detected":  True,
            "face_size_ok":   False,
            "blink_detected": False,
            "texture_ok":     False,
            "movement_ok":    False
        }

        # ── Check 1: Face size ────────────────────────────────
        if face_locations:
            checks["face_size_ok"] = self.check_face_size(
                face_locations[0], img.shape)

        # ── Check 2: Texture analysis ─────────────────────────
        if face_locations:
            texture_score = self.check_texture(img, face_locations[0])
            checks["texture_ok"]    = texture_score > self.TEXTURE_THRESHOLD
            checks["texture_score"] = round(texture_score, 2)

        # ── Check 3: EAR / Blink detection ───────────────────
        ear = self.calculate_ear(landmarks)
        self.ear_history[session_id].append(ear)

        if len(self.ear_history[session_id]) > 3:
            self.ear_history[session_id].pop(0)

        # Detect blink: EAR drops below threshold
        if ear < self.EAR_THRESHOLD:
            recent = self.ear_history[session_id]
            if len(recent) >= 2 and recent[-2] >= self.EAR_THRESHOLD:
                self.blink_counter[session_id] += 1
                logger.info("Blink detected! Session: " + session_id +
                            " Total: " + str(self.blink_counter[session_id]))

        checks["blink_detected"] = self.blink_counter[session_id] >= 1
        checks["blink_count"]    = self.blink_counter[session_id]
        checks["ear_value"]      = round(ear, 3)

        # ── Check 4: Head movement ────────────────────────────
        nose_pos = self.get_nose_position(landmarks)
        if nose_pos:
            self.head_positions[session_id].append(nose_pos)
            if len(self.head_positions[session_id]) > 20:
                self.head_positions[session_id].pop(0)

            if len(self.head_positions[session_id]) >= 5:
                positions = self.head_positions[session_id]
                x_vals    = [p[0] for p in positions]
                y_vals    = [p[1] for p in positions]
                x_range   = max(x_vals) - min(x_vals)
                y_range   = max(y_vals) - min(y_vals)
                # Natural micro-movements indicate real face
                checks["movement_ok"]    = x_range > 3 or y_range > 3
                checks["movement_range"] = round(float(x_range + y_range), 2)

        # ── Liveness Score ────────────────────────────────────
        score = 0
        if checks.get("face_size_ok"):   score += 20
        if checks.get("texture_ok"):     score += 30
        if checks.get("blink_detected"): score += 35
        if checks.get("movement_ok"):    score += 15

        is_live = score >= 65

        # ── Instruction for user ──────────────────────────────
        if not checks.get("face_size_ok"):
            instruction = "📏 Move closer to the camera"
        elif not checks.get("blink_detected"):
            instruction = "👁 Please blink naturally (" + \
                          str(self.blink_counter[session_id]) + "/1 blinks)"
        elif not checks.get("movement_ok"):
            instruction = "🔄 Please move your head slightly"
        elif not checks.get("texture_ok"):
            instruction = "💡 Improve lighting or remove obstructions"
        else:
            instruction = "✅ Liveness verified! Processing..."

        return {
            "live":          is_live,
            "face_detected": True,
            "blinks":        self.blink_counter[session_id],
            "frame":         frame_num,
            "confidence":    score,
            "ear":           round(ear, 3),
            "instruction":   instruction,
            "checks":        checks
        }

    def verify_liveness(self, session_id: str,
                         image_data: bytes,
                         required_blinks: int = 1) -> dict:
        """
        Final liveness verification check.
        Call this before recording attendance.
        """
        result = self.process_frame(session_id, image_data)
        blinks = self.blink_counter.get(session_id, 0)

        if not result["face_detected"]:
            return {
                "verified":    False,
                "reason":      "No face detected",
                "blinks":      blinks,
                "confidence":  0
            }

        if blinks < required_blinks:
            return {
                "verified":    False,
                "reason":      "Please blink " + str(required_blinks) +
                               " time(s). Detected: " + str(blinks),
                "blinks":      blinks,
                "confidence":  result["confidence"]
            }

        if not result["live"]:
            return {
                "verified":    False,
                "reason":      "Liveness check failed. Please try again.",
                "blinks":      blinks,
                "confidence":  result["confidence"]
            }

        # Clear session after successful verification
        self.reset_session(session_id)

        return {
            "verified":    True,
            "reason":      "✅ Liveness verified!",
            "blinks":      blinks,
            "confidence":  result["confidence"]
        }

    def reset_session(self, session_id: str):
        """Reset session data"""
        self.blink_counter.pop(session_id,  None)
        self.ear_history.pop(session_id,    None)
        self.frame_history.pop(session_id,  None)
        self.head_positions.pop(session_id, None)

    def get_session_status(self, session_id: str) -> dict:
        return {
            "session_id":  session_id,
            "blinks":      self.blink_counter.get(session_id, 0),
            "frames":      self.frame_history.get(session_id, 0),
            "active":      session_id in self.blink_counter
        }


liveness_service = LivenessService()
