from sqlmodel import Session, select
from models import User, Class, TeacherClassLink
from auth import get_password_hash
from database import engine, create_db_and_tables
import os


def init_data():
    # Reset the local demo database if possible.
    try:
        if os.path.exists("database.db"):
            os.remove("database.db")
    except Exception as e:
        print(f"Warning: Could not delete database.db: {e}. Trying to update existing DB.")

    create_db_and_tables()

    with Session(engine) as session:
        if not session.exec(select(User).where(User.username == "root")).first():
            root = User(
                username="root",
                password_hash=get_password_hash("root"),
                role="admin",
                full_name="System Admin",
            )
            session.add(root)
            print("Added root user")

        classes = [
            Class(name="CS2101", major="Computer Science"),
            Class(name="CS2102", major="Computer Science"),
            Class(name="SE2101", major="Software Engineering"),
            Class(name="IOT2101", major="Internet of Things"),
        ]

        db_classes = []
        for class_item in classes:
            existing = session.exec(select(Class).where(Class.name == class_item.name)).first()
            if not existing:
                session.add(class_item)
                db_classes.append(class_item)
                print(f"Added class {class_item.name}")
            else:
                db_classes.append(existing)
        session.commit()

        for class_item in db_classes:
            session.refresh(class_item)

        teachers = [
            User(
                username="teacher_a",
                password_hash=get_password_hash("123456"),
                role="teacher",
                full_name="Teacher A",
            ),
            User(
                username="teacher_b",
                password_hash=get_password_hash("123456"),
                role="teacher",
                full_name="Teacher B",
            ),
        ]

        db_teachers = []
        for teacher in teachers:
            existing = session.exec(select(User).where(User.username == teacher.username)).first()
            if not existing:
                session.add(teacher)
                db_teachers.append(teacher)
                print(f"Added teacher {teacher.username}")
            else:
                db_teachers.append(existing)
        session.commit()

        for teacher in db_teachers:
            session.refresh(teacher)

        links = [
            (db_teachers[0].id, db_classes[0].id),
            (db_teachers[0].id, db_classes[1].id),
            (db_teachers[1].id, db_classes[2].id),
        ]
        for teacher_id, class_id in links:
            exists = session.exec(
                select(TeacherClassLink).where(
                    TeacherClassLink.teacher_id == teacher_id,
                    TeacherClassLink.class_id == class_id,
                )
            ).first()
            if not exists:
                session.add(TeacherClassLink(teacher_id=teacher_id, class_id=class_id))
                print(f"Linked teacher {teacher_id} to class {class_id}")

        students = [
            User(
                username="student_01",
                password_hash=get_password_hash("123456"),
                role="student",
                full_name="Student One",
                student_id="2021001",
                class_id=db_classes[0].id,
                class_name=db_classes[0].name,
                major=db_classes[0].major,
            ),
            User(
                username="student_02",
                password_hash=get_password_hash("123456"),
                role="student",
                full_name="Student Two",
                student_id="2021002",
                class_id=db_classes[0].id,
                class_name=db_classes[0].name,
                major=db_classes[0].major,
            ),
            User(
                username="student_03",
                password_hash=get_password_hash("123456"),
                role="student",
                full_name="Student Three",
                student_id="2021003",
                class_id=db_classes[1].id,
                class_name=db_classes[1].name,
                major=db_classes[1].major,
            ),
            User(
                username="student_04",
                password_hash=get_password_hash("123456"),
                role="student",
                full_name="Student Four",
                student_id="2021004",
                class_id=db_classes[2].id,
                class_name=db_classes[2].name,
                major=db_classes[2].major,
            ),
        ]
        for student in students:
            existing = session.exec(select(User).where(User.username == student.username)).first()
            if not existing:
                session.add(student)
                print(f"Added student {student.username}")

        session.commit()
        print("Initialization complete!")


if __name__ == "__main__":
    init_data()
