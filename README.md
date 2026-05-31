# 🤖 AI-Powered HRM & Face Attendance System

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![React](https://img.shields.io/badge/React-18-cyan)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

A **complete commercial-grade HRM system** built for garments factories 
with 500+ employees. Features AI face recognition attendance, payroll, 
leave management, production tracking and BGMEA compliance reports.

## 🎯 Live Demo

> System runs on local network via Nginx  
> Access: `http://YOUR_SERVER_IP`

---

## ✨ Features

| Feature | Description |
|---|---|
| 👁 **Face Recognition** | AI attendance using dlib — 95%+ accuracy |
| 🛡️ **Anti-Spoofing** | Blink detection prevents photo attacks |
| 📊 **Live Dashboard** | Real-time React.js analytics |
| 💰 **Payroll System** | Auto salary + PDF pay slips |
| 📅 **Leave Management** | Apply, approve, balance tracking |
| ⏰ **Shift Management** | Morning/night/overtime tracking |
| 🏭 **Production Tracking** | Line targets, worker efficiency |
| 📜 **BGMEA Compliance** | Bangladesh labour law reports |
| 📷 **IP Camera Support** | RTSP stream auto punch |
| 📧 **Email Alerts** | Late/absent notifications |
| 📈 **Excel Export** | Salary sheets & reports |
| 🌐 **Production Deploy** | PostgreSQL + Nginx + systemd |

---

## 🛠️ Technology Stack

**Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL  
**Frontend:** React.js, JavaScript ES6+  
**AI/ML:** OpenCV, face_recognition (dlib), scipy  
**Server:** Nginx, systemd, Ubuntu 24.04  
**Security:** JWT, bcrypt, Anti-spoofing  
**Reports:** ReportLab (PDF), OpenPyXL (Excel)  

---

## 🚀 Quick Start

### Requirements
- Ubuntu 20.04+
- Python 3.10+
- Node.js 20+
- PostgreSQL 17+

### Installation

```bash
# Clone repository
git clone https://github.com/ar-sir23/hrm-face-attendance.git
cd hrm-face-attendance

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your settings

# Start backend
python main.py
```

```bash
# Frontend setup (new terminal)
cd frontend
npm install
npm start
```

Open: **http://localhost:3000**

---

## 📁 Project Structure

hrm-face-attendance/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── app/
│   │   ├── api/                # API routes
│   │   ├── models/             # Database models
│   │   └── services/           # Business logic
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/              # React pages
│       └── api.js              # API client
└── backup.sh                   # Auto backup script

---

## 📸 Screenshots

> Dashboard | Camera | Payroll | Reports | Production

---

## 🏭 Built For

- Garments / RMG factories (500+ workers)
- Corporate offices
- Schools & universities
- Any organization needing AI attendance

---

## 👨‍💻 Author

**Md. Abdur Rahman**  
Cybersecurity Analyst | AI & Full Stack Developer  
🔗 [GitHub](https://github.com/ar-sir23)  
💼 [Upwork Profile](#)

---

## 📄 License

MIT License — Free to use and modify
