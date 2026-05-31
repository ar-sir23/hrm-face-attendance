from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "HRM Face Attendance System"
    DATABASE_URL: str = "sqlite:///./hrm_attendance.db"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FACE_RECOGNITION_TOLERANCE: float = 0.5
    FACE_MODEL: str = "hog"
    FACE_IMAGES_DIR: str = "face_images"
    FACE_ENCODINGS_FILE: str = "face_encodings.pkl"
    CAMERA_INDEX: int = 0
    LATE_ARRIVAL_TIME: str = "09:30"
    OFFICE_START_TIME: str = "09:00"
    OFFICE_END_TIME: str = "18:00"
    MIN_WORK_HOURS: float = 8.0
    DUPLICATE_PUNCH_INTERVAL: int = 300
    MAX_UPLOAD_SIZE: int = 10485760
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MANAGER_EMAIL: str = ""
    SEND_LATE_ALERT: bool = True
    SEND_ABSENT_ALERT: bool = True
    SEND_DAILY_SUMMARY: bool = True
    DAILY_SUMMARY_TIME: str = "18:00"
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/jpg"]
    CAM_1_URL: str = "0"
    CAM_1_NAME: str = "Main Gate"
    CAM_2_URL: str = ""
    CAM_2_NAME: str = "Gate 2"
    CAM_PROCESS_EVERY_N_FRAMES: int = 10
    CAM_MIN_CONFIDENCE: float = 60.0
    CAM_SAVE_CAPTURES: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
