from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Class(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    major: str

class TeacherClassLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="user.id")
    class_id: int = Field(foreign_key="class.id")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="student") 
    full_name: Optional[str] = None
    student_id: Optional[str] = None # 学号
    class_id: Optional[int] = Field(default=None, foreign_key="class.id") # 关联班级ID
    class_name: Optional[str] = None # 冗余存储班级名，方便查询，或者仅用关联
    major: Optional[str] = None
    face_image_path: Optional[str] = None # 存储照片路径
    face_embedding: Optional[str] = Field(default=None, description="JSON序列化的人脸特征向量")

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    start_time: datetime
    end_time: datetime
    creator_id: Optional[int] = Field(default=None, foreign_key="user.id")
    target_classes: Optional[str] = None # 目标班级ID列表，逗号分隔 "1,2,3"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: float = Field(default=100.0) # 签到半径，米

class Attendance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    student_id: int = Field(foreign_key="user.id")
    status: str = Field(default="checked_in") 
    check_in_time: datetime = Field(default_factory=datetime.now)
    liveness_score: float = Field(default=0.0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
