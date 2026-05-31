from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class PayrollStatus(str, enum.Enum):
    DRAFT     = "DRAFT"
    APPROVED  = "APPROVED"
    PAID      = "PAID"
    CANCELLED = "CANCELLED"


class SalaryGrade(Base):
    """Salary grade / scale"""
    __tablename__ = "salary_grades"

    id            = Column(Integer, primary_key=True, index=True)
    grade_name    = Column(String(50), nullable=False)
    basic_salary  = Column(Float, nullable=False)
    house_rent    = Column(Float, default=0)
    medical       = Column(Float, default=0)
    transport     = Column(Float, default=0)
    food          = Column(Float, default=0)
    description   = Column(Text, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=func.now())

    employees = relationship("EmployeeSalary", back_populates="grade")


class EmployeeSalary(Base):
    """Employee salary configuration"""
    __tablename__ = "employee_salaries"

    id              = Column(Integer, primary_key=True, index=True)
    employee_id     = Column(Integer, ForeignKey("employees.id"), nullable=False, unique=True)
    grade_id        = Column(Integer, ForeignKey("salary_grades.id"), nullable=True)
    basic_salary    = Column(Float, nullable=False, default=12000)
    house_rent      = Column(Float, default=0)
    medical         = Column(Float, default=0)
    transport       = Column(Float, default=0)
    food            = Column(Float, default=0)
    overtime_rate   = Column(Float, default=1.5)
    tax_percentage  = Column(Float, default=0)
    pf_percentage   = Column(Float, default=0)
    effective_date  = Column(Date, nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=func.now())

    employee = relationship("Employee")
    grade    = relationship("SalaryGrade", back_populates="employees")


class PayrollRecord(Base):
    """Monthly payroll record per employee"""
    __tablename__ = "payroll_records"

    id                = Column(Integer, primary_key=True, index=True)
    employee_id       = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    year              = Column(Integer, nullable=False)
    month             = Column(Integer, nullable=False)

    # Working days
    total_working_days = Column(Integer, default=0)
    present_days       = Column(Integer, default=0)
    absent_days        = Column(Integer, default=0)
    late_days          = Column(Integer, default=0)
    leave_days         = Column(Integer, default=0)

    # Earnings
    basic_salary      = Column(Float, default=0)
    house_rent        = Column(Float, default=0)
    medical           = Column(Float, default=0)
    transport         = Column(Float, default=0)
    food              = Column(Float, default=0)
    overtime_amount   = Column(Float, default=0)
    bonus             = Column(Float, default=0)
    gross_salary      = Column(Float, default=0)

    # Deductions
    absent_deduction  = Column(Float, default=0)
    late_deduction    = Column(Float, default=0)
    tax_deduction     = Column(Float, default=0)
    pf_deduction      = Column(Float, default=0)
    other_deduction   = Column(Float, default=0)
    total_deduction   = Column(Float, default=0)

    # Net
    net_salary        = Column(Float, default=0)

    # Status
    status            = Column(Enum(PayrollStatus), default=PayrollStatus.DRAFT)
    approved_by       = Column(String(100), nullable=True)
    approved_at       = Column(DateTime, nullable=True)
    paid_at           = Column(DateTime, nullable=True)
    note              = Column(Text, nullable=True)
    created_at        = Column(DateTime, default=func.now())
    updated_at        = Column(DateTime, default=func.now(), onupdate=func.now())

    employee = relationship("Employee")
