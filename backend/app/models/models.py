from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class AttendanceType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    designation = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    face_image_path = Column(String(255), nullable=True)
    face_encoding_path = Column(String(255), nullable=True)
    face_registered = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    join_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    department = relationship("Department", back_populates="employees")
    attendance_logs = relationship("AttendanceLog", back_populates="employee")
    attendance_summary = relationship("AttendanceSummary", back_populates="employee")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    punch_time = Column(DateTime, nullable=False, default=func.now())
    punch_type = Column(Enum(AttendanceType), nullable=False)
    confidence_score = Column(Float, nullable=True)
    recognition_method = Column(String(20), default="FACE")
    captured_image_path = Column(String(255), nullable=True)
    camera_id = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())
    employee = relationship("Employee", back_populates="attendance_logs")

class AttendanceSummary(Base):
    __tablename__ = "attendance_summary"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    first_in = Column(DateTime, nullable=True)
    last_out = Column(DateTime, nullable=True)
    work_hours = Column(Float, default=0.0)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT)
    is_late = Column(Boolean, default=False)
    late_minutes = Column(Integer, default=0)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    employee = relationship("Employee", back_populates="attendance_summary")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="hr")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
