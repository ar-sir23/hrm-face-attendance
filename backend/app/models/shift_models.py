from sqlalchemy import Column, Integer, String, DateTime, Boolean, Time, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ShiftType(str, enum.Enum):
    MORNING  = "MORNING"
    EVENING  = "EVENING"
    NIGHT    = "NIGHT"
    GENERAL  = "GENERAL"
    CUSTOM   = "CUSTOM"


class Shift(Base):
    """Shift definition"""
    __tablename__ = "shifts"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    shift_type  = Column(Enum(ShiftType), default=ShiftType.GENERAL)
    start_time  = Column(String(10), nullable=False)   # "06:00"
    end_time    = Column(String(10), nullable=False)   # "14:00"
    late_after  = Column(String(10), nullable=False)   # "06:15"
    grace_minutes = Column(Integer, default=15)
    overtime_after_hours = Column(Integer, default=8)
    is_night_shift = Column(Boolean, default=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())

    # Relationships
    employee_shifts = relationship("EmployeeShift", back_populates="shift")


class EmployeeShift(Base):
    """Which employee is assigned to which shift"""
    __tablename__ = "employee_shifts"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    shift_id    = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())

    # Relationships
    employee = relationship("Employee")
    shift    = relationship("Shift", back_populates="employee_shifts")


class OvertimeRecord(Base):
    """Overtime tracking per employee per day"""
    __tablename__ = "overtime_records"

    id              = Column(Integer, primary_key=True, index=True)
    employee_id     = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date            = Column(Date, nullable=False)
    shift_id        = Column(Integer, ForeignKey("shifts.id"), nullable=True)
    regular_hours   = Column(Integer, default=8)
    actual_hours    = Column(Integer, default=0)
    overtime_hours  = Column(Integer, default=0)
    overtime_rate   = Column(Integer, default=150)  # % of hourly rate
    approved        = Column(Boolean, default=False)
    approved_by     = Column(String(100), nullable=True)
    note            = Column(String(255), nullable=True)
    created_at      = Column(DateTime, default=func.now())

    employee = relationship("Employee")
    shift    = relationship("Shift")


class ShiftRotation(Base):
    """Rotation schedule for employees"""
    __tablename__ = "shift_rotations"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())

    schedules = relationship("RotationSchedule", back_populates="rotation")


class RotationSchedule(Base):
    """Day-by-day schedule in a rotation"""
    __tablename__ = "rotation_schedules"

    id          = Column(Integer, primary_key=True, index=True)
    rotation_id = Column(Integer, ForeignKey("shift_rotations.id"), nullable=False)
    week_number = Column(Integer, nullable=False)   # 1, 2, 3...
    day_of_week = Column(Integer, nullable=False)   # 0=Mon, 6=Sun
    shift_id    = Column(Integer, ForeignKey("shifts.id"), nullable=True)
    is_off      = Column(Boolean, default=False)

    rotation = relationship("ShiftRotation", back_populates="schedules")
    shift    = relationship("Shift")
