import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.username = settings.MAIL_USERNAME
        self.password = settings.MAIL_PASSWORD
        self.from_email = settings.MAIL_FROM
        self.server = settings.MAIL_SERVER
        self.port = settings.MAIL_PORT

    async def send_email(self, to_email: str, subject: str, html_body: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = self.from_email
            msg["To"]      = to_email
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=self.server,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=True
            )
            logger.info("Email sent to: " + to_email)
            return True
        except Exception as e:
            logger.error("Email error: " + str(e))
            return False

    async def send_late_alert(self, employee_name: str, employee_id: str,
                               arrival_time: str, late_minutes: int,
                               manager_email: str):
        subject = "Late Arrival Alert — " + employee_name
        html = """
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
          <div style="background:#d29922;padding:20px;color:white">
            <h2 style="margin:0">⏰ Late Arrival Alert</h2>
            <p style="margin:4px 0 0">""" + datetime.now().strftime("%B %d, %Y") + """</p>
          </div>
          <div style="padding:24px">
            <p style="font-size:15px">The following employee has arrived late today:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
              <tr style="background:#f9f9f9">
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Employee Name</td>
                <td style="padding:10px 14px;border:1px solid #eee">""" + employee_name + """</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Employee ID</td>
                <td style="padding:10px 14px;border:1px solid #eee">""" + employee_id + """</td>
              </tr>
              <tr style="background:#f9f9f9">
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Arrival Time</td>
                <td style="padding:10px 14px;border:1px solid #eee">""" + arrival_time + """</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Late By</td>
                <td style="padding:10px 14px;color:#d29922;font-weight:bold;border:1px solid #eee">""" + str(late_minutes) + """ minutes</td>
              </tr>
            </table>
            <p style="color:#666;font-size:13px">This is an automated alert from FaceHRM Attendance System.</p>
          </div>
        </div>
        """
        return await self.send_email(manager_email, subject, html)

    async def send_absent_alert(self, employee_name: str, employee_id: str,
                                 manager_email: str):
        subject = "Absent Alert — " + employee_name
        html = """
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
          <div style="background:#f85149;padding:20px;color:white">
            <h2 style="margin:0">❌ Employee Absent Alert</h2>
            <p style="margin:4px 0 0">""" + datetime.now().strftime("%B %d, %Y") + """</p>
          </div>
          <div style="padding:24px">
            <p style="font-size:15px">The following employee is absent today:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
              <tr style="background:#f9f9f9">
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Employee Name</td>
                <td style="padding:10px 14px;border:1px solid #eee">""" + employee_name + """</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Employee ID</td>
                <td style="padding:10px 14px;border:1px solid #eee">""" + employee_id + """</td>
              </tr>
              <tr style="background:#f9f9f9">
                <td style="padding:10px 14px;font-weight:bold;border:1px solid #eee">Date</td>
                <td style="padding:10px 14px;border:1px solid #eee">""" + datetime.now().strftime("%B %d, %Y") + """</td>
              </tr>
            </table>
            <p style="color:#666;font-size:13px">This is an automated alert from FaceHRM Attendance System.</p>
          </div>
        </div>
        """
        return await self.send_email(manager_email, subject, html)

    async def send_daily_summary(self, manager_email: str, stats: dict, late_list: list, absent_list: list):
        subject = "Daily Attendance Summary — " + datetime.now().strftime("%B %d, %Y")
        late_rows = ""
        for emp in late_list:
            late_rows += """
            <tr>
              <td style="padding:8px 12px;border:1px solid #eee">""" + emp.get("employee_name","") + """</td>
              <td style="padding:8px 12px;border:1px solid #eee;color:#d29922">""" + str(emp.get("late_minutes","")) + """ min late</td>
            </tr>"""

        absent_rows = ""
        for emp in absent_list:
            absent_rows += """
            <tr>
              <td style="padding:8px 12px;border:1px solid #eee">""" + emp.get("employee_name","") + """</td>
              <td style="padding:8px 12px;border:1px solid #eee;color:#f85149">Absent</td>
            </tr>"""

        html = """
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
          <div style="background:#0ea5e9;padding:20px;color:white">
            <h2 style="margin:0">📊 Daily Attendance Summary</h2>
            <p style="margin:4px 0 0">""" + datetime.now().strftime("%B %d, %Y") + """</p>
          </div>
          <div style="padding:24px">
            <div style="display:flex;gap:16px;margin-bottom:24px">
              <div style="flex:1;background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px;font-weight:bold;color:#16a34a">""" + str(stats.get("present",0)) + """</div>
                <div style="color:#15803d;font-size:13px">Present</div>
              </div>
              <div style="flex:1;background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px;font-weight:bold;color:#dc2626">""" + str(stats.get("absent",0)) + """</div>
                <div style="color:#b91c1c;font-size:13px">Absent</div>
              </div>
              <div style="flex:1;background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px;font-weight:bold;color:#d97706">""" + str(stats.get("late",0)) + """</div>
                <div style="color:#b45309;font-size:13px">Late</div>
              </div>
              <div style="flex:1;background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px;font-weight:bold;color:#2563eb">""" + str(stats.get("present_percentage",0)) + """%</div>
                <div style="color:#1d4ed8;font-size:13px">Rate</div>
              </div>
            </div>
            """ + ("""
            <h3 style="color:#d29922;margin-bottom:8px">⏰ Late Arrivals</h3>
            <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
              <tr style="background:#f9f9f9"><th style="padding:8px 12px;border:1px solid #eee;text-align:left">Employee</th><th style="padding:8px 12px;border:1px solid #eee;text-align:left">Status</th></tr>
              """ + late_rows + """
            </table>""" if late_rows else "") + ("""
            <h3 style="color:#f85149;margin-bottom:8px">❌ Absent Employees</h3>
            <table style="width:100%;border-collapse:collapse">
              <tr style="background:#f9f9f9"><th style="padding:8px 12px;border:1px solid #eee;text-align:left">Employee</th><th style="padding:8px 12px;border:1px solid #eee;text-align:left">Status</th></tr>
              """ + absent_rows + """
            </table>""" if absent_rows else "") + """
            <p style="color:#666;font-size:13px;margin-top:20px">This is an automated daily report from FaceHRM Attendance System.</p>
          </div>
        </div>
        """
        return await self.send_email(manager_email, subject, html)

email_service = EmailService()
