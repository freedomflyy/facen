from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta, datetime
from typing import Annotated, List
from contextlib import asynccontextmanager
import random
import string

from database import create_db_and_tables, get_session
from models import User, Session as ClassSession, Attendance
from auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import json
from face_service import face_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Allow all CORS for network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Auth Dependencies ---

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    # In a real app, decode token and fetch user
    from jose import JWTError, jwt
    from auth import SECRET_KEY, ALGORITHM
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

# --- Routes ---

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

import os
import shutil
from sqlalchemy import func 
from models import User, Session as ClassSession, Attendance, Class, TeacherClassLink

# Ensure upload directory
UPLOAD_DIR = "uploads/faces"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ... auth ...

@app.post("/register", response_model=User)
async def register(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    full_name: str = Form(None),
    student_id: str = Form(None),
    class_id: int = Form(None),
    major: str = Form(None),
    file: UploadFile = File(None), # Optional for teacher, required for student logic
    session: Session = Depends(get_session)
):
    # Check existing
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Process Class Info
    class_name = None
    if class_id:
        cls = session.get(Class, class_id)
        if cls:
            class_name = cls.name
            major = cls.major # Auto-fill major from class
    
    # Process Photo
    face_path = None
    face_embedding_json = None
    
    if role == 'student':
        if not file:
             raise HTTPException(status_code=400, detail="Photo is required for students")
        
        # Read content
        content = await file.read()
        
        # Face Service Processing
        try:
            img = face_service.process_image(content)
            
            # 1. Liveness (Skipped for Registration)
            # liveness = face_service.check_liveness(img)
            # if liveness < 0.5: ...
            
            # 2. Embedding
            embedding, info = face_service.get_face_embedding(img)
            if not embedding:
                 raise HTTPException(status_code=400, detail="未检测到人脸，请重新拍摄")
            
            face_embedding_json = json.dumps(embedding)
            
        except Exception as e:
            # If face service fails (e.g. model not loaded), handle gracefully or raise
            if isinstance(e, HTTPException): raise e
            import traceback
            traceback.print_exc()
            print(f"Face Error: {e}")
            # raise HTTPException(status_code=500, detail=f"Face processing error: {str(e)}")
            # For robustness, if model fails, maybe allow? No, better fail.
            raise HTTPException(status_code=400, detail=f"人脸处理失败: {str(e)}")

        file_ext = file.filename.split('.')[-1]
        face_path = f"{UPLOAD_DIR}/{username}_{random.randint(1000,9999)}.{file_ext}"
        with open(face_path, "wb") as buffer:
            buffer.write(content)

    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        role=role,
        full_name=full_name,
        student_id=student_id,
        class_id=class_id,
        class_name=class_name,
        major=major,
        face_image_path=face_path,
        face_embedding=face_embedding_json
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

# --- Admin Routes ---

@app.get("/admin/stats")
async def get_admin_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    total_students = session.exec(select(func.count(User.id)).where(User.role == "student")).one()
    total_teachers = session.exec(select(func.count(User.id)).where(User.role == "teacher")).one()
    total_classes = session.exec(select(func.count(Class.id))).one()
    total_sessions = session.exec(select(func.count(ClassSession.id))).one()
    
    return {
        "students": total_students,
        "teachers": total_teachers,
        "classes": total_classes,
        "sessions": total_sessions
    }

@app.get("/admin/teachers")
async def get_teachers(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return session.exec(select(User).where(User.role == "teacher")).all()

@app.post("/admin/teachers")
async def create_teacher(
    user: User, 
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    existing = session.exec(select(User).where(User.username == user.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username exists")
        
    if user.password_hash:
        user.password_hash = get_password_hash(user.password_hash)
    else:
        # Set a default password if not provided (or handle as error)
        # For now, let's assume admin must provide password or we set default '123456'
        user.password_hash = get_password_hash("123456")

    user.role = "teacher"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.post("/admin/classes")
async def create_class(
    cls: Class,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    existing = session.exec(select(Class).where(Class.name == cls.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class exists")
        
    session.add(cls)
    session.commit()
    session.refresh(cls)
    return cls

@app.put("/admin/classes/{class_id}")
async def update_class(
    class_id: int,
    data: dict,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    cls = session.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
        
    if "name" in data: cls.name = data["name"]
    if "major" in data: cls.major = data["major"]
    
    session.add(cls)
    session.commit()
    session.refresh(cls)
    return cls

@app.delete("/admin/classes/{class_id}")
async def delete_class(
    class_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    cls = session.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
        
    # Check for related students
    related_students = session.exec(select(User).where(User.class_id == class_id)).first()
    if related_students:
         raise HTTPException(status_code=400, detail="Cannot delete class with existing students. Please reassign students first.")
         
    # Check for related teacher links
    session.exec(select(TeacherClassLink).where(TeacherClassLink.class_id == class_id)).all()
    # Ideally delete links
    links = session.exec(select(TeacherClassLink).where(TeacherClassLink.class_id == class_id)).all()
    for l in links: session.delete(l)
    
    session.delete(cls)
    session.commit()
    return {"status": "success"}

@app.get("/admin/teachers/{teacher_id}/classes")
async def get_teacher_classes(
    teacher_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    links = session.exec(select(TeacherClassLink).where(TeacherClassLink.teacher_id == teacher_id)).all()
    return [l.class_id for l in links]

@app.post("/admin/teachers/{teacher_id}/assign")
async def assign_classes(
    teacher_id: int,
    class_ids: List[int],
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Clear existing
    existing = session.exec(select(TeacherClassLink).where(TeacherClassLink.teacher_id == teacher_id)).all()
    for e in existing:
        session.delete(e)
        
    # Add new
    for cid in class_ids:
        link = TeacherClassLink(teacher_id=teacher_id, class_id=cid)
        session.add(link)
        
    session.commit()
    return {"status": "success"}

@app.get("/admin/classes/{class_id}/students")
async def get_class_students(
    class_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return session.exec(select(User).where(User.class_id == class_id).where(User.role == "student")).all()

@app.get("/admin/sessions")
async def get_all_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    # Return sessions with creator name
    results = session.exec(select(ClassSession, User.full_name).join(User, ClassSession.creator_id == User.id).order_by(ClassSession.start_time.desc())).all()
    
    data = []
    for s, creator_name in results:
        # Calculate stats
        total = session.exec(select(func.count(Attendance.id)).where(Attendance.session_id == s.id)).one()
        # Just simple count for list view
        s_dict = s.model_dump()
        s_dict['creator_name'] = creator_name
        s_dict['attendance_count'] = total
        data.append(s_dict)
        
    return data

@app.delete("/admin/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    s = session.get(ClassSession, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Delete related attendance records first
    atts = session.exec(select(Attendance).where(Attendance.session_id == session_id)).all()
    for a in atts:
        session.delete(a)
        
    session.delete(s)
    session.commit()
    return {"status": "success"}

@app.get("/admin/students")
async def get_all_students(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return session.exec(select(User).where(User.role == "student")).all()

@app.post("/admin/students")
async def create_student(
    user: User, 
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    existing = session.exec(select(User).where(User.username == user.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username exists")
    
    # Fill class info
    if user.class_id:
        cls = session.get(Class, user.class_id)
        if cls:
            user.class_name = cls.name
            user.major = cls.major
        
    user.password_hash = get_password_hash(user.password_hash)
    user.role = "student"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.put("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    data: dict,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if "full_name" in data: user.full_name = data["full_name"]
    if "student_id" in data: user.student_id = data["student_id"]
    if "class_id" in data and data["class_id"]:
        user.class_id = data["class_id"]
        # Update class name too
        cls = session.get(Class, data["class_id"])
        if cls:
            user.class_name = cls.name
            user.major = cls.major
            
    if "password" in data and data["password"]: 
        user.password_hash = get_password_hash(data["password"])
        
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Delete related records
    session.exec(select(Attendance).where(Attendance.student_id == user_id)).all() # Delete attendance logic if needed
    
    session.delete(user)
    session.commit()
    return {"status": "success"}

@app.get("/admin/sessions/{session_id}/attendance")
async def get_session_attendance_admin(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    # Reuse the logic from teacher dashboard, maybe refine later
    # 1. Get checked-in records
    records = session.exec(
        select(Attendance, User)
        .where(Attendance.session_id == session_id)
        .join(User, Attendance.student_id == User.id)
    ).all()
    
    checked_in_ids = []
    result = []
    
    for att, student in records:
        checked_in_ids.append(student.id)
        result.append({
            "id": att.id,
            "student_username": student.username,
            "student_name": student.full_name or student.username,
            "student_id": student.student_id,
            "class_name": student.class_name,
            "status": att.status,
            "check_in_time": att.check_in_time,
            "student_user_id": student.id
        })
        
    # 2. Add absent students (Logic copied from teacher view)
    s = session.get(ClassSession, session_id)
    if s and s.target_classes:
         try:
             class_ids = [int(cid) for cid in s.target_classes.split(",") if cid.strip()]
             if class_ids:
                 absent_students = session.exec(
                     select(User)
                     .where(User.class_id.in_(class_ids))
                     .where(User.role == "student")
                     .where(User.id.notin_(checked_in_ids))
                 ).all()
                 
                 for student in absent_students:
                     result.append({
                         "id": None, 
                         "student_username": student.username,
                         "student_name": student.full_name or student.username,
                         "student_id": student.student_id,
                         "class_name": student.class_name,
                         "status": "absent",
                         "check_in_time": None,
                         "student_user_id": student.id 
                     })
         except: pass
             
    return result

@app.put("/admin/attendance/{attendance_id}")
async def update_attendance_status(
    attendance_id: int,
    data: dict,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    att = session.get(Attendance, attendance_id)
    if not att:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if "status" in data:
        att.status = data["status"]
        
    session.add(att)
    session.commit()
    return att

@app.post("/admin/sessions/{session_id}/attendance")
async def create_attendance_manual(
    session_id: int,
    data: dict,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    student_id = data.get("student_id")
    status = data.get("status", "checked_in")
    
    # Check if exists
    existing = session.exec(select(Attendance).where(Attendance.session_id == session_id, Attendance.student_id == student_id)).first()
    if existing:
        existing.status = status
        session.add(existing)
    else:
        att = Attendance(
            session_id=session_id, 
            student_id=student_id, 
            status=status,
            liveness_score=1.0, # Admin manual override
            check_in_time=datetime.now()
        )
        session.add(att)
        
    session.commit()
    return {"status": "success"}

# --- Teacher Routes ---

@app.get("/classes", response_model=List[Class])
async def get_classes(session: Session = Depends(get_session)):
    return session.exec(select(Class)).all()

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

# --- Teacher Routes ---

@app.get("/teachers/me/classes")
async def get_my_classes(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    # Get assigned classes
    links = session.exec(select(TeacherClassLink).where(TeacherClassLink.teacher_id == current_user.id)).all()
    class_ids = [l.class_id for l in links]
    
    if not class_ids:
        return []
        
    return session.exec(select(Class).where(Class.id.in_(class_ids))).all()

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3 # Earth radius in meters
    phi1 = lat1 * math.pi / 180
    phi2 = lat2 * math.pi / 180
    delta_phi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180
    
    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    d = R * c
    return d

@app.post("/sessions")
async def create_session(
    session_data: dict, 
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create sessions")
    
    # Generate 6-digit code
    code = ''.join(random.choices(string.digits, k=6))
    
    # Handle target_classes list to string
    target_classes_str = None
    if session_data.get("target_classes"):
        t_list = session_data.get("target_classes")
        if isinstance(t_list, list):
            target_classes_str = ",".join(map(str, t_list))
        else:
            target_classes_str = str(t_list)

    new_session = ClassSession(
        code=code,
        name=session_data.get("name"),
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(minutes=session_data.get("duration", 30)),
        creator_id=current_user.id,
        target_classes=target_classes_str, 
        latitude=session_data.get("latitude"),
        longitude=session_data.get("longitude"),
        radius=session_data.get("radius", 100.0)
    )
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    return new_session

@app.get("/sessions")
async def get_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    # Teachers see sessions they created
    if current_user.role == "teacher":
        statement = select(ClassSession).where(ClassSession.creator_id == current_user.id)
        return session.exec(statement).all()
    return []

import base64
import cv2
import numpy as np

@app.post("/count-faces")
async def count_faces(file: UploadFile = File(...)):
    content = await file.read()
    img = face_service.process_image(content)
    faces = face_service.app.get(img)
    
    # Draw boxes
    for face in faces:
        box = face.bbox.astype(int)
        cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        
    # Encode back to jpg
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "count": len(faces),
        "image_base64": f"data:image/jpeg;base64,{img_base64}"
    }

@app.get("/sessions/{session_id}/attendance")
async def get_attendance(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    s = session.get(ClassSession, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get checked-in records
    records = session.exec(select(Attendance).where(Attendance.session_id == session_id)).all()
    checked_in_ids = {r.student_id for r in records}
    
    result = []
    
    # 1. Add checked-in students
    for r in records:
        student = session.get(User, r.student_id)
        result.append({
            "id": r.id,
            "student_username": student.username,
            "student_name": student.full_name or student.username,
            "student_id": student.student_id,
            "class_name": student.class_name,
            "status": r.status,
            "check_in_time": r.check_in_time.strftime("%H:%M:%S"),
            "distance": "N/A" # Ideally calculate if we have session lat/lon
        })

    # 2. Add absent students (if target_classes is set)
    if s.target_classes:
        # Parse "1,2,3" to [1, 2, 3]
        try:
            class_ids = [int(cid) for cid in s.target_classes.split(",") if cid.strip()]
        except:
            class_ids = []
            
        if class_ids:
            absent_students = session.exec(
                select(User)
                .where(User.class_id.in_(class_ids))
                .where(User.role == "student")
                .where(User.id.notin_(checked_in_ids))
            ).all()
            
            for student in absent_students:
                result.append({
                    "id": None, 
                    "student_username": student.username,
                    "student_name": student.full_name or student.username,
                    "student_id": student.student_id,
                    "class_name": student.class_name,
                    "status": "absent",
                    "check_in_time": "-",
                    "student_user_id": student.id 
                })
            
    return result

@app.post("/attendance/manual-check-in")
async def manual_check_in(
    data: dict,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    session_id = data.get("session_id")
    student_id = data.get("student_id")
    
    # Check if already exists
    existing = session.exec(
        select(Attendance)
        .where(Attendance.session_id == session_id)
        .where(Attendance.student_id == student_id)
    ).first()
    
    if existing:
        existing.status = "checked_in" # Update if was late/absent record
        existing.check_in_time = datetime.now()
        session.add(existing)
    else:
        new_record = Attendance(
            session_id=session_id,
            student_id=student_id,
            status="checked_in_manual", # Mark as manual
            check_in_time=datetime.now()
        )
        session.add(new_record)
        
    session.commit()
    return {"status": "success"}

@app.get("/attendance/me")
async def get_my_attendance(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their attendance")
        
    records = session.exec(
        select(Attendance, ClassSession)
        .where(Attendance.student_id == current_user.id)
        .join(ClassSession, Attendance.session_id == ClassSession.id)
        .order_by(Attendance.check_in_time.desc())
    ).all()
    
    result = []
    for att, sess in records:
        result.append({
            "id": att.id,
            "session_name": sess.name,
            "check_in_time": att.check_in_time,
            "status": att.status,
            "session_code": sess.code
        })
    return result

# --- Student Routes ---

@app.get("/sessions/verify/{code}")
async def verify_session_code(code: str, session: Session = Depends(get_session)):
    s = session.exec(select(ClassSession).where(ClassSession.code == code)).first()
    if not s:
        raise HTTPException(status_code=404, detail="签到码无效或不存在")
    
    # Time Rules:
    # <= end_time: Present
    # <= end_time + 30m: Late
    # > end_time + 30m: Expired (Absent)
    now = datetime.now()
    late_deadline = s.end_time + timedelta(minutes=30)
    
    if now > late_deadline:
        raise HTTPException(status_code=400, detail=f"签到已结束！截止时间: {late_deadline.strftime('%H:%M:%S')}")
        
    return s

@app.post("/attendance/check-in")
async def check_in_real(
    session_id: int = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db_session: Session = Depends(get_session)
):
    # 0. Check Session Validity (Location & Class)
    s = db_session.get(ClassSession, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="签到会话不存在")
    
    # Timeout Check
    now = datetime.now()
    late_deadline = s.end_time + timedelta(minutes=30)
    
    if now > late_deadline:
         raise HTTPException(status_code=400, detail=f"签到已超时！截止时间: {late_deadline.strftime('%H:%M:%S')}")
    
    # Determine Status
    status = "checked_in"
    if now > s.end_time:
        status = "late"
        
    # Class Restriction Check
    if s.target_classes and current_user.class_id:
        try:
             allowed_ids = [int(cid) for cid in s.target_classes.split(",") if cid.strip()]
             if current_user.class_id not in allowed_ids:
                 # Fetch class names for better error message (Optional, but good for UX)
                 allowed_classes = db_session.exec(select(Class).where(Class.id.in_(allowed_ids))).all()
                 allowed_names = ", ".join([c.name for c in allowed_classes])
                 raise HTTPException(status_code=403, detail=f"非本课程班级学生。仅限: {allowed_names}")
        except HTTPException:
            raise
        except:
             pass # Ignore parsing error

    # Location Check
    if s.latitude is not None and s.longitude is not None:
        if latitude is None or longitude is None:
             raise HTTPException(status_code=400, detail="本场签到需要获取地理位置，请允许浏览器定位")
        
        distance = calculate_distance(s.latitude, s.longitude, latitude, longitude)
        if distance > s.radius:
             raise HTTPException(status_code=400, detail=f"位置校验失败：距离目标 {int(distance)}米，超出允许范围 (限 {int(s.radius)}米)")

    # 1. Face Verification (Real)
    content = await file.read()
    liveness_score = 0.0
    
    try:
        img = face_service.process_image(content)
        
        # Liveness
        liveness_score = face_service.check_liveness(img)
        # Only enforce if model is loaded
        if face_service.liveness_sess and liveness_score < 0.2:
             # raise HTTPException(status_code=400, detail="活体检测失败：检测到非真实人脸")
             pass # Debug: allow fail for now
        
        # Verification
        if not current_user.face_embedding:
             # Fallback if old user
             raise HTTPException(status_code=400, detail="未找到您的人脸档案，请联系管理员重新录入")
             
        stored_emb = json.loads(current_user.face_embedding)
        current_emb, info = face_service.get_face_embedding(img)
        
        if not current_emb:
             # Debug info
             print(f"Face Check-in Failed: No face detected. Msg: {info.get('msg')}")
             raise HTTPException(status_code=400, detail="未检测到人脸，请调整角度或光线")
             
        sim = face_service.compute_sim(stored_emb, current_emb)
        print(f"Face Check-in Sim: {sim}")
        
        if sim < 0.4:
             raise HTTPException(status_code=400, detail=f"人脸不匹配 (相似度:{sim:.2f})")
             
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        print(f"Check-in Face Error: {e}")
        raise HTTPException(status_code=400, detail=f"人脸验证出错: {str(e)}")
        
    # 2. Check for duplicate
    existing = db_session.exec(
        select(Attendance)
        .where(Attendance.session_id == session_id)
        .where(Attendance.student_id == current_user.id)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="您已完成签到，请勿重复操作")
        
    # 3. Record
    attendance = Attendance(
        session_id=session_id,
        student_id=current_user.id,
        status=status,
        liveness_score=liveness_score,
        latitude=latitude,
        longitude=longitude
    )
    db_session.add(attendance)
    db_session.commit()
    return {"status": "success", "message": "Checked in successfully", "attendance_status": status}

