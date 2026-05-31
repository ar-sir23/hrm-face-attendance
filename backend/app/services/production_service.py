from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
import calendar
import logging
from typing import Optional, List
from app.models.production_models import (
    ProductionLine, ProductionTarget, ProductionRecord,
    LineWorkerAssignment, WorkerEfficiency, LineStatus
)
from app.models.models import Employee, AttendanceSummary, AttendanceStatus

logger = logging.getLogger(__name__)


class ProductionService:

    def create_default_lines(self, db: Session):
        if db.query(ProductionLine).count() > 0:
            return
        lines = [
            {"name": "Line A",  "code": "LINE-A", "floor": "Floor 1", "capacity": 30},
            {"name": "Line B",  "code": "LINE-B", "floor": "Floor 1", "capacity": 30},
            {"name": "Line C",  "code": "LINE-C", "floor": "Floor 2", "capacity": 25},
            {"name": "Line D",  "code": "LINE-D", "floor": "Floor 2", "capacity": 25},
            {"name": "Line E",  "code": "LINE-E", "floor": "Floor 3", "capacity": 20},
            {"name": "Cutting", "code": "CUTTING","floor": "Floor 1", "capacity": 15},
            {"name": "Finishing","code":"FINISH", "floor": "Floor 3", "capacity": 20},
            {"name": "QC Line", "code": "QC",     "floor": "Floor 3", "capacity": 10},
        ]
        for l in lines:
            db.add(ProductionLine(**l))
        db.commit()
        logger.info("Default production lines created")

    def set_daily_target(self, db: Session, line_id: int,
                          target_date: date, product_name: str,
                          target_pieces: int, target_hours: float = 8.0,
                          notes: str = None) -> ProductionTarget:
        existing = db.query(ProductionTarget).filter(
            ProductionTarget.line_id == line_id,
            ProductionTarget.date    == target_date
        ).first()
        if existing:
            existing.product_name  = product_name
            existing.target_pieces = target_pieces
            existing.target_hours  = target_hours
            existing.notes         = notes
            db.commit()
            return existing
        target = ProductionTarget(
            line_id=line_id, date=target_date,
            product_name=product_name,
            target_pieces=target_pieces,
            target_hours=target_hours, notes=notes
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        return target

    def record_hourly_production(self, db: Session, line_id: int,
                                  record_date: date, hour: int,
                                  pieces_made: int, defective: int = 0,
                                  workers_present: int = 0,
                                  recorded_by: str = None) -> ProductionRecord:
        existing = db.query(ProductionRecord).filter(
            ProductionRecord.line_id == line_id,
            ProductionRecord.date    == record_date,
            ProductionRecord.hour    == hour
        ).first()
        if existing:
            existing.pieces_made     = pieces_made
            existing.defective       = defective
            existing.workers_present = workers_present
            existing.recorded_by     = recorded_by
            db.commit()
            return existing
        record = ProductionRecord(
            line_id=line_id, date=record_date, hour=hour,
            pieces_made=pieces_made, defective=defective,
            workers_present=workers_present, recorded_by=recorded_by
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info("Production recorded: Line " + str(line_id) +
                    " Hour " + str(hour) + " Pieces " + str(pieces_made))
        return record

    def get_line_daily_summary(self, db: Session,
                                line_id: int, target_date: date) -> dict:
        line   = db.query(ProductionLine).filter(
            ProductionLine.id == line_id).first()
        if not line:
            return {}

        target = db.query(ProductionTarget).filter(
            ProductionTarget.line_id == line_id,
            ProductionTarget.date    == target_date
        ).first()

        records = db.query(ProductionRecord).filter(
            ProductionRecord.line_id == line_id,
            ProductionRecord.date    == target_date
        ).order_by(ProductionRecord.hour).all()

        total_pieces    = sum(r.pieces_made for r in records)
        total_defective = sum(r.defective   for r in records)
        target_pieces   = target.target_pieces if target else 0
        efficiency      = round(
            (total_pieces / target_pieces * 100) if target_pieces > 0 else 0, 1)
        quality         = round(
            ((total_pieces - total_defective) / total_pieces * 100)
            if total_pieces > 0 else 100, 1)

        # Worker count from attendance
        assignments = db.query(LineWorkerAssignment).filter(
            LineWorkerAssignment.line_id   == line_id,
            LineWorkerAssignment.is_active == True
        ).all()
        worker_ids = [a.employee_id for a in assignments]
        present_workers = 0
        if worker_ids:
            present_workers = db.query(AttendanceSummary).filter(
                AttendanceSummary.employee_id.in_(worker_ids),
                AttendanceSummary.date   == target_date,
                AttendanceSummary.status != AttendanceStatus.ABSENT
            ).count()

        return {
            "line_id":         line.id,
            "line_name":       line.name,
            "line_code":       line.code,
            "floor":           line.floor,
            "date":            target_date.isoformat(),
            "product":         target.product_name if target else "N/A",
            "target_pieces":   target_pieces,
            "actual_pieces":   total_pieces,
            "defective":       total_defective,
            "good_pieces":     total_pieces - total_defective,
            "efficiency":      efficiency,
            "quality_score":   quality,
            "total_workers":   len(assignments),
            "present_workers": present_workers,
            "status":          line.status.value,
            "hourly_records": [
                {
                    "hour":            r.hour,
                    "time":            str(r.hour).zfill(2) + ":00",
                    "pieces_made":     r.pieces_made,
                    "defective":       r.defective,
                    "workers_present": r.workers_present
                }
                for r in records
            ]
        }

    def get_factory_dashboard(self, db: Session,
                               target_date: date) -> dict:
        lines   = db.query(ProductionLine).filter(
            ProductionLine.is_active == True).all()
        summaries = []
        total_target = 0
        total_actual = 0
        total_workers = 0
        total_present = 0

        for line in lines:
            summary = self.get_line_daily_summary(db, line.id, target_date)
            if summary:
                summaries.append(summary)
                total_target  += summary.get("target_pieces",  0)
                total_actual  += summary.get("actual_pieces",  0)
                total_workers += summary.get("total_workers",  0)
                total_present += summary.get("present_workers",0)

        overall_efficiency = round(
            (total_actual / total_target * 100) if total_target > 0 else 0, 1)

        return {
            "date":                target_date.isoformat(),
            "total_lines":         len(lines),
            "total_target_pieces": total_target,
            "total_actual_pieces": total_actual,
            "overall_efficiency":  overall_efficiency,
            "total_workers":       total_workers,
            "total_present":       total_present,
            "lines":               summaries
        }

    def calculate_worker_efficiency(self, db: Session,
                                     employee_id: int,
                                     target_date: date,
                                     actual_pieces: int,
                                     target_pieces: int = None,
                                     quality_score: float = 100.0,
                                     incentive_per_piece: float = 0.5) -> WorkerEfficiency:
        # Get line assignment
        assignment = db.query(LineWorkerAssignment).filter(
            LineWorkerAssignment.employee_id == employee_id,
            LineWorkerAssignment.is_active   == True
        ).first()
        line_id = assignment.line_id if assignment else None

        # Get target from line if not provided
        if not target_pieces and line_id:
            line_target = db.query(ProductionTarget).filter(
                ProductionTarget.line_id == line_id,
                ProductionTarget.date    == target_date
            ).first()
            if line_target:
                # Per worker target
                workers = db.query(LineWorkerAssignment).filter(
                    LineWorkerAssignment.line_id   == line_id,
                    LineWorkerAssignment.is_active == True
                ).count()
                target_pieces = (line_target.target_pieces //
                                 workers) if workers > 0 else 0

        target_pieces  = target_pieces or 100
        efficiency_pct = round(
            (actual_pieces / target_pieces * 100) if target_pieces > 0 else 0, 1)

        # Incentive — only if above 100% efficiency
        incentive = 0
        if efficiency_pct > 100:
            extra_pieces = actual_pieces - target_pieces
            incentive    = round(extra_pieces * incentive_per_piece, 2)

        existing = db.query(WorkerEfficiency).filter(
            WorkerEfficiency.employee_id == employee_id,
            WorkerEfficiency.date        == target_date
        ).first()

        if existing:
            existing.actual_pieces   = actual_pieces
            existing.target_pieces   = target_pieces
            existing.efficiency_pct  = efficiency_pct
            existing.quality_score   = quality_score
            existing.incentive_earned = incentive
            existing.line_id         = line_id
            db.commit()
            return existing

        record = WorkerEfficiency(
            employee_id=employee_id, line_id=line_id,
            date=target_date, target_pieces=target_pieces,
            actual_pieces=actual_pieces, efficiency_pct=efficiency_pct,
            quality_score=quality_score, incentive_earned=incentive
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def get_top_performers(self, db: Session,
                            year: int, month: int, limit: int = 10) -> list:
        first = date(year, month, 1)
        last  = date(year, month, calendar.monthrange(year, month)[1])
        records = db.query(
            WorkerEfficiency.employee_id,
            func.avg(WorkerEfficiency.efficiency_pct).label("avg_efficiency"),
            func.sum(WorkerEfficiency.actual_pieces).label("total_pieces"),
            func.sum(WorkerEfficiency.incentive_earned).label("total_incentive"),
            func.count(WorkerEfficiency.id).label("days_recorded")
        ).filter(
            WorkerEfficiency.date >= first,
            WorkerEfficiency.date <= last
        ).group_by(
            WorkerEfficiency.employee_id
        ).order_by(
            func.avg(WorkerEfficiency.efficiency_pct).desc()
        ).limit(limit).all()

        result = []
        for r in records:
            emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
            if emp:
                result.append({
                    "employee_id":     emp.employee_id,
                    "employee_name":   emp.full_name,
                    "avg_efficiency":  round(float(r.avg_efficiency), 1),
                    "total_pieces":    int(r.total_pieces),
                    "total_incentive": round(float(r.total_incentive), 2),
                    "days_recorded":   int(r.days_recorded)
                })
        return result

    def get_monthly_line_report(self, db: Session,
                                 line_id: int,
                                 year: int, month: int) -> dict:
        first   = date(year, month, 1)
        last    = date(year, month, calendar.monthrange(year, month)[1])
        line    = db.query(ProductionLine).filter(
            ProductionLine.id == line_id).first()
        if not line:
            return {}

        records = db.query(ProductionRecord).filter(
            ProductionRecord.line_id == line_id,
            ProductionRecord.date    >= first,
            ProductionRecord.date    <= last
        ).all()

        targets = db.query(ProductionTarget).filter(
            ProductionTarget.line_id == line_id,
            ProductionTarget.date    >= first,
            ProductionTarget.date    <= last
        ).all()

        total_target = sum(t.target_pieces for t in targets)
        total_actual = sum(r.pieces_made   for r in records)
        total_defect = sum(r.defective     for r in records)

        return {
            "line_name":       line.name,
            "year":            year,
            "month":           month,
            "total_target":    total_target,
            "total_actual":    total_actual,
            "total_defective": total_defect,
            "total_good":      total_actual - total_defect,
            "avg_efficiency":  round(
                (total_actual / total_target * 100)
                if total_target > 0 else 0, 1),
            "avg_quality":     round(
                ((total_actual - total_defect) / total_actual * 100)
                if total_actual > 0 else 100, 1),
            "working_days":    len(set(r.date for r in records))
        }


production_service = ProductionService()
