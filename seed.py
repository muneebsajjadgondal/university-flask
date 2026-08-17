"""Seed script: creates demo departments, instructors, students, courses,
teacher assignments, enrollments, attendance, and marks — plus one admin.

Run with: python seed.py
"""
from datetime import date
from app import create_app
from extensions import db
from models import Department, User, Teacher, Student, Course, TeacherCourse, Enrollment, Attendance, Marks

DOMAIN = "university.edu"


def mk_email(first, last, tag=""):
    return f"{first.lower()}.{last.lower()}{tag}@{DOMAIN}"


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Admin
        admin_user = User(username="admin", email=mk_email("admin", "office"), role="admin", status="active")
        admin_user.set_password("password123")
        db.session.add(admin_user)

        # Departments
        cs = Department(name="Computer Science", code="CS", building="Block A")
        ee = Department(name="Electrical Engineering", code="EE", building="Block B")
        bba = Department(name="Business Administration", code="BBA", building="Block C")
        math = Department(name="Mathematics", code="MATH", building="Block A")
        db.session.add_all([cs, ee, bba, math])
        db.session.flush()

        # Instructors
        def make_teacher(username, first, last, title, dept, hire):
            u = User(username=username, email=mk_email(first, last), role="teacher", status="active")
            u.set_password("password123")
            db.session.add(u)
            db.session.flush()
            t = Teacher(user_id=u.id, full_name=f"{first} {last}", title=title, department_id=dept.id, hire_date=hire)
            db.session.add(t)
            db.session.flush()
            return t

        t_ayesha = make_teacher("jsmith", "Ayesha", "Khan", "Assistant Professor", cs, date(2019, 8, 1))
        t_bilal = make_teacher("akhan", "Bilal", "Ahmed", "Professor", cs, date(2015, 1, 15))
        t_sara = make_teacher("smalik", "Sara", "Malik", "Lecturer", ee, date(2021, 9, 1))
        t_usman = make_teacher("utariq", "Usman", "Tariq", "Associate Professor", bba, date(2017, 3, 10))

        # Courses
        cs101 = Course(code="CS101", title="Introduction to Programming", credit_hours=3, department_id=cs.id, capacity=45)
        cs204 = Course(code="CS204", title="Database Management Systems", credit_hours=3, department_id=cs.id, capacity=40)
        cs310 = Course(code="CS310", title="Operating Systems", credit_hours=4, department_id=cs.id, capacity=35)
        ee150 = Course(code="EE150", title="Circuit Analysis", credit_hours=3, department_id=ee.id, capacity=30)
        bba101 = Course(code="BBA101", title="Principles of Management", credit_hours=3, department_id=bba.id, capacity=50)
        db.session.add_all([cs101, cs204, cs310, ee150, bba101])
        db.session.flush()

        SEM = "Fall 2025"
        db.session.add_all([
            TeacherCourse(teacher_id=t_ayesha.id, course_id=cs101.id, semester=SEM),
            TeacherCourse(teacher_id=t_bilal.id, course_id=cs204.id, semester=SEM),
            TeacherCourse(teacher_id=t_bilal.id, course_id=cs310.id, semester=SEM),
            TeacherCourse(teacher_id=t_sara.id, course_id=ee150.id, semester=SEM),
            TeacherCourse(teacher_id=t_usman.id, course_id=bba101.id, semester=SEM),
        ])

        # Students
        def make_student(username, roll, first, last, gender, dept, year, sem, dob):
            u = User(username=username, email=mk_email(first, last, ".s"), role="student", status="active")
            u.set_password("password123")
            db.session.add(u)
            db.session.flush()
            s = Student(
                user_id=u.id, roll_number=roll, full_name=f"{first} {last}",
                email=mk_email(first, last, ".s"), gender=gender, department_id=dept.id,
                enrollment_year=year, current_semester=sem, date_of_birth=dob, status="active",
            )
            db.session.add(s)
            db.session.flush()
            return s

        s1 = make_student("sfarooq", "SP24-CS-001", "Zeeshan", "Riaz", "Male", cs, 2024, 3, date(2004, 5, 12))
        s2 = make_student("mnaeem", "SP24-CS-002", "Zara", "Iqbal", "Female", cs, 2024, 3, date(2004, 11, 2))
        s3 = make_student("ali_r", "SP23-EE-014", "Hamza", "Sheikh", "Male", ee, 2023, 5, date(2003, 7, 19))
        s4 = make_student("mnoor", "SP23-BBA-032", "Mahnoor", "Noor", "Female", bba, 2023, 5, date(2003, 2, 28))

        # Enrollments
        enrollments = [
            Enrollment(student_id=s1.id, course_id=cs101.id, semester=SEM, status="Active"),
            Enrollment(student_id=s1.id, course_id=cs204.id, semester=SEM, status="Active"),
            Enrollment(student_id=s2.id, course_id=cs101.id, semester=SEM, status="Active"),
            Enrollment(student_id=s2.id, course_id=cs204.id, semester=SEM, status="Active"),
            Enrollment(student_id=s3.id, course_id=ee150.id, semester=SEM, status="Active"),
            Enrollment(student_id=s4.id, course_id=bba101.id, semester=SEM, status="Completed"),
        ]
        db.session.add_all(enrollments)

        # Attendance (a few sample days for CS101)
        for d in [date(2025, 9, 1), date(2025, 9, 3), date(2025, 9, 8)]:
            db.session.add(Attendance(student_id=s1.id, course_id=cs101.id, date=d, status="Present"))
            db.session.add(Attendance(student_id=s2.id, course_id=cs101.id, date=d, status="Present" if d != date(2025, 9, 8) else "Absent"))

        # Marks
        db.session.add_all([
            Marks(student_id=s1.id, course_id=cs101.id, semester=SEM, assignment_marks=18, midterm_marks=27, final_marks=38),
            Marks(student_id=s2.id, course_id=cs101.id, semester=SEM, assignment_marks=15, midterm_marks=22, final_marks=30),
            Marks(student_id=s4.id, course_id=bba101.id, semester=SEM, assignment_marks=19, midterm_marks=28, final_marks=40),
        ])

        db.session.commit()
        print("Seed complete.")
        print(f"Admin login   -> {mk_email('admin', 'office')} / password123 (username: admin)")
        print(f"Teacher login -> jsmith / password123")
        print(f"Student login -> sfarooq / password123")


if __name__ == "__main__":
    run()
