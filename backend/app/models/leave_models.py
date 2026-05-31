from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class LeaveType(str, enum.Enum):
    ANNUAL      = "ANNUAL"
    SICK        = "SICK"
    CASUAL      = "CASUAL"
    MATERNITY   = "MATERNITY"
    PATERNITY   = "PATERNITY"
    UNPAID      = "UNPAID"
    EMERGENCY   = "EMERGENCY"


class LeaveStatus(str, enum.Enum):
    PENDING   = "PENDING"
    APPROVED  = "APPROVED"
    REJECTED  = "REJECTED"
    CANCELLED = "CANCELLED"


class LeavePolicy(Base):
    """Leave policy — how many days per year per type"""
    __tablename__ = "leave_policies"

    id              = Column(Integer, primary_key=True, index=True)
    leave_type      = Column(Enum(LeaveType), nullable=False, unique=True)
    days_per_year   = Column(Integer, nullable=False)
    carry_forward   = Column(Boolean, default=False)
    max_carry_days  = Column(Integer, default=0)
    paid            = Column(Boolean, default=True)
    description     = Column(Text, nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=func.now())


class LeaveBalance(Base):
    """Employee leave balance per year"""
    __tablename__ = "leave_balances"

    id            = Column(Integer, primary_key=True, index=True)
    employee_id   = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    year          = Column(Integer, nullable=False)
    leave_type    = Column(Enum(LeaveType), nullable=False)
    total_days    = Column(Float, default=0)
    used_days     = Column(Float, default=0)
    remaining_days = Column(Float, default=0)
    created_at    = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())

    employee = relationship("Employee")


class LeaveApplication(Base):
    """Leave application by employee"""
    __tablename__ = "leave_applications"

    id            = Column(Integer, primary_key=True, index=True)
    employee_id   = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type    = Column(Enum(LeaveType), nullable=False)
    start_date    = Column(Date, nullable=False)
    end_date      = Column(Date, nullable=False)
    total_days    = Column(Float, nullable=False)
    reason        = Column(Text, nullable=False)
    status        = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)

    # Approval
    approved_by   = Column(String(100), nullable=True)
    approved_at   = Column(DateTime, nullable=True)
    reject_reason = Column(Text, nullable=True)

    # Contact during leave
    contact_number = Column(String(20), nullable=True)
    handover_to    = Column(String(100), nullable=True)

    created_at    = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())

    employee = relationship("Employee")


class Holiday(Base):
    """Public holidays and office holidays"""
    __tablename__ = "holidays"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    date        = Column(Date, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_optional = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=func.now())
