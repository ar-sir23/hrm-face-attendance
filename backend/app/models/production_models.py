from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class LineStatus(str, enum.Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"
    BREAK    = "BREAK"
    MAINTENANCE = "MAINTENANCE"


class ProductionLine(Base):
    """Factory production line"""
    __tablename__ = "production_lines"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    code          = Column(String(20),  unique=True, nullable=False)
    floor         = Column(String(50),  nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    supervisor_id = Column(Integer, ForeignKey("employees.id"),   nullable=True)
    capacity      = Column(Integer, default=30)   # max workers
    status        = Column(Enum(LineStatus), default=LineStatus.ACTIVE)
    description   = Column(Text, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=func.now())

    department = relationship("Department")
    supervisor = relationship("Employee", foreign_keys=[supervisor_id])
    targets    = relationship("ProductionTarget",   back_populates="line")
    records    = relationship("ProductionRecord",   back_populates="line")
    workers    = relationship("LineWorkerAssignment", back_populates="line")


class ProductionTarget(Base):
    """Daily production target per line"""
    __tablename__ = "production_targets"

    id            = Column(Integer, primary_key=True, index=True)
    line_id       = Column(Integer, ForeignKey("production_lines.id"), nullable=False)
    date          = Column(Date, nullable=False)
    product_name  = Column(String(100), nullable=False)
    target_pieces = Column(Integer, nullable=False)
    target_hours  = Column(Float, default=8.0)
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=func.now())

    line = relationship("ProductionLine", back_populates="targets")


class ProductionRecord(Base):
    """Actual production record per line per hour"""
    __tablename__ = "production_records"

    id             = Column(Integer, primary_key=True, index=True)
    line_id        = Column(Integer, ForeignKey("production_lines.id"), nullable=False)
    date           = Column(Date, nullable=False)
    hour           = Column(Integer, nullable=False)    # 0-23
    pieces_made    = Column(Integer, default=0)
    defective      = Column(Integer, default=0)
    workers_present= Column(Integer, default=0)
    recorded_by    = Column(String(100), nullable=True)
    notes          = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=func.now())

    line = relationship("ProductionLine", back_populates="records")


class LineWorkerAssignment(Base):
    """Which worker is assigned to which line"""
    __tablename__ = "line_worker_assignments"

    id          = Column(Integer, primary_key=True, index=True)
    line_id     = Column(Integer, ForeignKey("production_lines.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"),        nullable=False)
    role        = Column(String(50), default="WORKER")   # WORKER, HELPER, QC
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())

    line     = relationship("ProductionLine", back_populates="workers")
    employee = relationship("Employee")


class WorkerEfficiency(Base):
    """Daily worker efficiency record"""
    __tablename__ = "worker_efficiency"

    id             = Column(Integer, primary_key=True, index=True)
    employee_id    = Column(Integer, ForeignKey("employees.id"),        nullable=False)
    line_id        = Column(Integer, ForeignKey("production_lines.id"), nullable=True)
    date           = Column(Date, nullable=False)
    target_pieces  = Column(Integer, default=0)
    actual_pieces  = Column(Integer, default=0)
    efficiency_pct = Column(Float, default=0)
    quality_score  = Column(Float, default=100)   # % good pieces
    incentive_earned = Column(Float, default=0)
    notes          = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=func.now())

    employee = relationship("Employee")
    line     = relationship("ProductionLine")
