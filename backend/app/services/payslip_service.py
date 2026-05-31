from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import calendar
import io
import logging
from sqlalchemy.orm import Session
from app.models.payroll_models import PayrollRecord
from app.models.models import Employee

logger = logging.getLogger(__name__)

TEAL  = colors.HexColor("#00D4AA")
DARK  = colors.HexColor("#0D1117")
GREY  = colors.HexColor("#8B949E")
GREEN = colors.HexColor("#3FB950")
RED   = colors.HexColor("#F85149")
WHITE = colors.white
BLACK = colors.black


class PayslipService:

    def generate_payslip(self, db: Session, employee_id: int,
                          year: int, month: int,
                          company_name: str = "Garments Factory Ltd.") -> bytes:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            raise ValueError("Employee not found")

        record = db.query(PayrollRecord).filter(
            PayrollRecord.employee_id == employee_id,
            PayrollRecord.year  == year,
            PayrollRecord.month == month
        ).first()
        if not record:
            raise ValueError("Payroll not calculated yet. Run calculate first.")

        month_name = datetime(year, month, 1).strftime("%B %Y")
        buf        = io.BytesIO()
        doc        = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=1.5*cm, leftMargin=1.5*cm,
            topMargin=1.5*cm,   bottomMargin=1.5*cm
        )

        styles  = getSampleStyleSheet()
        story   = []

        # ── Company Header ─────────────────────────────────────
        header_data = [[
            Paragraph(
                "<font size='16'><b>" + company_name + "</b></font><br/>"
                "<font size='9' color='grey'>HR Department — Payroll System</font>",
                ParagraphStyle("h", alignment=TA_LEFT)
            ),
            Paragraph(
                "<font size='14'><b>PAY SLIP</b></font><br/>"
                "<font size='10' color='grey'>" + month_name + "</font>",
                ParagraphStyle("r", alignment=TA_RIGHT)
            )
        ]]
        header_table = Table(header_data, colWidths=[10*cm, 7*cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,-1), DARK),
            ("TEXTCOLOR",   (0,0), (-1,-1), WHITE),
            ("PADDING",     (0,0), (-1,-1), 14),
            ("ROUNDEDCORNERS", [8]),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.4*cm))

        # ── Employee Info ───────────────────────────────────────
        dept = emp.department.name if emp.department else "N/A"
        info_data = [
            ["Employee Name",  emp.full_name,      "Employee ID", emp.employee_id],
            ["Designation",    emp.designation or "N/A", "Department", dept],
            ["Pay Period",     month_name,          "Pay Date",   datetime.now().strftime("%d %b %Y")],
            ["Working Days",   str(record.total_working_days),
             "Days Present",   str(record.present_days)],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 6.5*cm, 3.5*cm, 3.5*cm])
        info_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (0,-1), colors.HexColor("#161B22")),
            ("BACKGROUND",    (2,0), (2,-1), colors.HexColor("#161B22")),
            ("TEXTCOLOR",     (0,0), (0,-1), TEAL),
            ("TEXTCOLOR",     (2,0), (2,-1), TEAL),
            ("TEXTCOLOR",     (1,0), (1,-1), BLACK),
            ("TEXTCOLOR",     (3,0), (3,-1), BLACK),
            ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",      (2,0), (2,-1), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("PADDING",       (0,0), (-1,-1), 7),
            ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.HexColor("#F6F8FA"), WHITE]),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.4*cm))

        # ── Earnings & Deductions Side by Side ─────────────────
        earn_rows = [
            ["EARNINGS",          "Amount (BDT)"],
            ["Basic Salary",      "{:,.2f}".format(record.basic_salary)],
            ["House Rent",        "{:,.2f}".format(record.house_rent)],
            ["Medical Allowance", "{:,.2f}".format(record.medical)],
            ["Transport",         "{:,.2f}".format(record.transport)],
            ["Food Allowance",    "{:,.2f}".format(record.food)],
            ["Overtime Pay",      "{:,.2f}".format(record.overtime_amount)],
            ["Bonus",             "{:,.2f}".format(record.bonus)],
            ["GROSS SALARY",      "{:,.2f}".format(record.gross_salary)],
        ]

        ded_rows = [
            ["DEDUCTIONS",        "Amount (BDT)"],
            ["Absent Deduction",  "{:,.2f}".format(record.absent_deduction)],
            ["Late Deduction",    "{:,.2f}".format(record.late_deduction)],
            ["Income Tax",        "{:,.2f}".format(record.tax_deduction)],
            ["Provident Fund",    "{:,.2f}".format(record.pf_deduction)],
            ["Other Deduction",   "{:,.2f}".format(record.other_deduction)],
            ["", ""],
            ["", ""],
            ["TOTAL DEDUCTION",   "{:,.2f}".format(record.total_deduction)],
        ]

        earn_table = Table(earn_rows, colWidths=[5.5*cm, 3*cm])
        earn_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), DARK),
            ("BACKGROUND",   (0,-1),(-1,-1), colors.HexColor("#0D2818")),
            ("TEXTCOLOR",    (0,0), (-1,0), TEAL),
            ("TEXTCOLOR",    (0,-1),(-1,-1), GREEN),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTNAME",     (0,-1),(-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("ALIGN",        (1,0), (1,-1), "RIGHT"),
            ("PADDING",      (0,0), (-1,-1), 6),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS",(0,1),(-1,-2), [colors.HexColor("#F6F8FA"), WHITE]),
        ]))

        ded_table = Table(ded_rows, colWidths=[5.5*cm, 3*cm])
        ded_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), DARK),
            ("BACKGROUND",   (0,-1),(-1,-1), colors.HexColor("#2D0D0D")),
            ("TEXTCOLOR",    (0,0), (-1,0), RED),
            ("TEXTCOLOR",    (0,-1),(-1,-1), RED),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTNAME",     (0,-1),(-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("ALIGN",        (1,0), (1,-1), "RIGHT"),
            ("PADDING",      (0,0), (-1,-1), 6),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS",(0,1),(-1,-2), [colors.HexColor("#F6F8FA"), WHITE]),
        ]))

        combined = Table([[earn_table, Spacer(0.3*cm, 1), ded_table]])
        combined.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
        story.append(combined)
        story.append(Spacer(1, 0.4*cm))

        # ── Net Salary Box ──────────────────────────────────────
        net_data = [[
            Paragraph("<font size='12'><b>NET SALARY PAYABLE</b></font>",
                      ParagraphStyle("nl", alignment=TA_LEFT, textColor=WHITE)),
            Paragraph("<font size='18'><b>BDT {:,.2f}</b></font>".format(record.net_salary),
                      ParagraphStyle("nr", alignment=TA_RIGHT, textColor=TEAL))
        ]]
        net_table = Table(net_data, colWidths=[9*cm, 8.5*cm])
        net_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), DARK),
            ("PADDING",    (0,0), (-1,-1), 14),
            ("ROUNDEDCORNERS", [6]),
        ]))
        story.append(net_table)
        story.append(Spacer(1, 0.5*cm))

        # ── Attendance Summary ──────────────────────────────────
        att_data = [
            ["Working Days", "Present", "Absent", "Late", "Leave"],
            [
                str(record.total_working_days),
                str(record.present_days),
                str(record.absent_days),
                str(record.late_days),
                str(record.leave_days)
            ]
        ]
        att_table = Table(att_data, colWidths=[3.5*cm]*5)
        att_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#161B22")),
            ("TEXTCOLOR",   (0,0), (-1,0), TEAL),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("PADDING",     (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ("TEXTCOLOR",   (1,1), (1,1), GREEN),
            ("TEXTCOLOR",   (2,1), (2,1), RED),
            ("TEXTCOLOR",   (3,1), (3,1), colors.HexColor("#D29922")),
            ("FONTNAME",    (0,1), (-1,1), "Helvetica-Bold"),
        ]))
        story.append(Paragraph("<b>Attendance Summary</b>",
                               ParagraphStyle("as", fontSize=10, textColor=GREY)))
        story.append(Spacer(1, 0.2*cm))
        story.append(att_table)
        story.append(Spacer(1, 0.8*cm))

        # ── Signatures ─────────────────────────────────────────
        sig_data = [[
            Paragraph("________________________<br/><font size='8' color='grey'>Employee Signature</font>",
                      ParagraphStyle("s1", alignment=TA_CENTER)),
            Paragraph("________________________<br/><font size='8' color='grey'>HR Manager</font>",
                      ParagraphStyle("s2", alignment=TA_CENTER)),
            Paragraph("________________________<br/><font size='8' color='grey'>Accounts</font>",
                      ParagraphStyle("s3", alignment=TA_CENTER)),
        ]]
        sig_table = Table(sig_data, colWidths=[5.8*cm]*3)
        sig_table.setStyle(TableStyle([("PADDING", (0,0), (-1,-1), 10)]))
        story.append(sig_table)

        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREY))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "This is a computer generated pay slip. Generated on " +
            datetime.now().strftime("%d %B %Y %H:%M") +
            " by FaceHRM System.",
            ParagraphStyle("footer", fontSize=7, textColor=GREY, alignment=TA_CENTER)
        ))

        doc.build(story)
        buf.seek(0)
        logger.info("Pay slip generated: " + emp.full_name + " " + month_name)
        return buf.getvalue()


payslip_service = PayslipService()
