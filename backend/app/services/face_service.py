import face_recognition
import cv2
import numpy as np
import pickle
import os
import logging
import asyncio
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

# Global singleton
_instance = None

def get_face_service():
    global _instance
    if _instance is None:
        _instance = FaceRecognitionService()
    return _instance

class FaceRecognitionService:
    def __init__(self):
        self.known_face_encodings = []
        self.known_employee_ids = []
        self.known_employee_names = []
        os.makedirs(settings.FACE_IMAGES_DIR, exist_ok=True)
        self._load_encodings()
        logger.info("Face Recognition Service started")

    def _load_encodings(self):
        if os.path.exists(settings.FACE_ENCODINGS_FILE):
            try:
                with open(settings.FACE_ENCODINGS_FILE, "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get("encodings", [])
                    self.known_employee_ids = data.get("employee_ids", [])
                    self.known_employee_names = data.get("names", [])
                logger.info(str(len(self.known_face_encodings)) + " employee faces loaded")
            except Exception as e:
                logger.error("Load error: " + str(e))

    def _save_encodings(self):
        with open(settings.FACE_ENCODINGS_FILE, "wb") as f:
            pickle.dump({
                "encodings": self.known_face_encodings,
                "employee_ids": self.known_employee_ids,
                "names": self.known_employee_names
            }, f)
        logger.info("Encodings saved: " + str(len(self.known_face_encodings)) + " faces")

    def reload_encodings(self):
        self._load_encodings()

    def register_face(self, employee_id, employee_name, image_data):
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image, model=settings.FACE_MODEL)
            if len(face_locations) == 0:
                return {"success": False, "message": "No face found in image"}
            if len(face_locations) > 1:
                return {"success": False, "message": "Multiple faces found, use single face photo"}
            encodings = face_recognition.face_encodings(rgb_image, face_locations)
            if not encodings:
                return {"success": False, "message": "Could not create encoding"}
            face_encoding = encodings[0]
            if employee_id in self.known_employee_ids:
                idx = self.known_employee_ids.index(employee_id)
                self.known_face_encodings[idx] = face_encoding
                self.known_employee_names[idx] = employee_name
                logger.info("Updated face for: " + employee_name)
            else:
                self.known_face_encodings.append(face_encoding)
                self.known_employee_ids.append(employee_id)
                self.known_employee_names.append(employee_name)
                logger.info("Registered new face for: " + employee_name)
            image_path = os.path.join(settings.FACE_IMAGES_DIR, employee_id + ".jpg")
            cv2.imwrite(image_path, image)
            self._save_encodings()
            logger.info("Total registered: " + str(len(self.known_face_encodings)))
            return {
                "success": True,
                "message": employee_name + " face registered successfully",
                "image_path": image_path,
                "total_registered": len(self.known_face_encodings)
            }
        except Exception as e:
            logger.error("Register error: " + str(e))
            return {"success": False, "message": str(e)}

    def recognize_face(self, image_data):
        try:
            self._load_encodings()
            if not self.known_face_encodings:
                return {"recognized": False, "faces": [], "message": "No faces registered"}
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image, model=settings.FACE_MODEL)
            if not face_locations:
                return {"recognized": False, "faces": [], "message": "No face found in image"}
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            results = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_idx = int(np.argmin(distances))
                best_dist = float(distances[best_idx])
                confidence = round(max(0.0, (1.0 - best_dist) * 100), 2)
                top = face_location[0]
                right = face_location[1]
                bottom = face_location[2]
                left = face_location[3]
                logger.info("Best distance: " + str(best_dist) + " confidence: " + str(confidence))
                if best_dist <= settings.FACE_RECOGNITION_TOLERANCE:
                    results.append({
                        "recognized": True,
                        "employee_id": self.known_employee_ids[best_idx],
                        "employee_name": self.known_employee_names[best_idx],
                        "confidence": confidence,
                        "face_location": {
                            "top": top, "right": right,
                            "bottom": bottom, "left": left
                        }
                    })
                else:
                    results.append({
                        "recognized": False,
                        "employee_name": "Unknown",
                        "confidence": confidence,
                        "distance": best_dist
                    })
            any_recognized = any(r["recognized"] for r in results)
            return {
                "recognized": any_recognized,
                "faces": results,
                "total_faces": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Recognize error: " + str(e))
            return {"recognized": False, "faces": [], "message": str(e)}

    async def process_frame_async(self, image_bytes):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.recognize_face, image_bytes)

    def remove_employee_face(self, employee_id):
        if employee_id in self.known_employee_ids:
            idx = self.known_employee_ids.index(employee_id)
            self.known_face_encodings.pop(idx)
            self.known_employee_ids.pop(idx)
            self.known_employee_names.pop(idx)
            self._save_encodings()
            img_path = os.path.join(settings.FACE_IMAGES_DIR, employee_id + ".jpg")
            if os.path.exists(img_path):
                os.remove(img_path)
            return True
        return False

    def get_registered_count(self):
        self._load_encodings()
        return len(self.known_face_encodings)
