from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import date
from app.database import get_db
from app.models.models import Employee, Department
from app.services.face_service import get_face_service
from app.config import settings

router = APIRouter()
face_service = get_face_service()

class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class EmployeeCreate(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    department_id: Optional[int] = None
    join_date: Optional[date] = None

@router.post("/departments")
async def create_department(dept: DepartmentCreate, db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.code == dept.code).first():
        raise HTTPException(status_code=400, detail="এই কোডের বিভাগ আগেই আছে")
    d = Department(**dept.dict())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d

@router.get("/departments")
async def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

@router.post("/")
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    if db.query(Employee).filter(Employee.employee_id == employee.employee_id).first():
        raise HTTPException(status_code=400, detail="এই ID-এর কর্মী আগেই আছে")
    emp = Employee(**employee.dict())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp

@router.get("/stats/face-registration")
async def face_stats(db: Session = Depends(get_db)):
    total = db.query(Employee).filter(Employee.is_active == True).count()
    registered = db.query(Employee).filter(
        Employee.is_active == True,
        Employee.face_registered == True
    ).count()
    return {
        "total_employees": total,
        "face_registered": registered,
        "not_registered": total - registered,
        "registration_percentage": round((registered / total * 100) if total > 0 else 0, 1)
    }

@router.get("/")
async def get_employees(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(Employee)
    if active_only:
        q = q.filter(Employee.is_active == True)
    return q.order_by(Employee.first_name).all()

@router.get("/{employee_id}")
async def get_employee(employee_id: str, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="কর্মী পাওয়া যায়নি")
    return emp

@router.post("/{employee_id}/register-face")
async def register_face(
    employee_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="কর্মী পাওয়া যায়নি")
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="শুধু JPG ও PNG গ্রহণযোগ্য")
    image_data = await file.read()
    result = face_service.register_face(employee_id, emp.full_name, image_data)
    if result["success"]:
        emp.face_registered = True
        emp.face_image_path = result.get("image_path")
        db.commit()
        return result
    raise HTTPException(status_code=400, detail=result["message"])

@router.delete("/{employee_id}/remove-face")
async def remove_face(employee_id: str, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="কর্মী পাওয়া যায়নি")
    if face_service.remove_employee_face(employee_id):
        emp.face_registered = False
        db.commit()
        return {"message": "মুখ নিবন্ধন বাতিল হয়েছে"}
    raise HTTPException(status_code=400, detail="বাতিল করা যায়নি")
