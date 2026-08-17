import secrets
from datetime import datetime, date, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    building = db.Column(db.String(120))

    teachers = db.relationship("Teacher", back_populates="department")
    students = db.relationship("Student", back_populates="department")
    courses = db.relationship("Course", back_populates="department")


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    status = db.Column(db.String(20), nullable=False, default="active")  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_profile = db.relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    student_profile = db.relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def is_active_account(self):
        return self.status == "active"


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30))
    title = db.Column(db.String(60), default="Lecturer")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    hire_date = db.Column(db.Date)

    user = db.relationship("User", back_populates="teacher_profile")
    department = db.relationship("Department", back_populates="teachers")
    course_assignments = db.relationship(
        "TeacherCourse", back_populates="teacher", cascade="all, delete-orphan"
    )


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30))
    gender = db.Column(db.String(10), default="Other")
    date_of_birth = db.Column(db.Date)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    enrollment_year = db.Column(db.Integer)
    current_semester = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="active")  # active, graduated, suspended

    user = db.relationship("User", back_populates="student_profile")
    department = db.relationship("Department", back_populates="students")
    enrollments = db.relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    attendance_records = db.relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )
    marks_records = db.relationship(
        "Marks", back_populates="student", cascade="all, delete-orphan"
    )


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(160), nullable=False)
    credit_hours = db.Column(db.Integer, nullable=False, default=3)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    capacity = db.Column(db.Integer, default=40)

    department = db.relationship("Department", back_populates="courses")
    teacher_assignments = db.relationship(
        "TeacherCourse", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    attendance_records = db.relationship(
        "Attendance", back_populates="course", cascade="all, delete-orphan"
    )
    marks_records = db.relationship(
        "Marks", back_populates="course", cascade="all, delete-orphan"
    )


class TeacherCourse(db.Model):
    """Which teacher is assigned to teach which course, in which semester."""
    __tablename__ = "teacher_courses"
    __table_args__ = (
        db.UniqueConstraint("teacher_id", "course_id", "semester", name="uq_teacher_course_semester"),
    )

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester = db.Column(db.String(40), nullable=False)

    teacher = db.relationship("Teacher", back_populates="course_assignments")
    course = db.relationship("Course", back_populates="teacher_assignments")


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "semester", name="uq_student_course_semester"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(20), default="Active")  # Active, Completed, Dropped
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "date", name="uq_student_course_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), nullable=False, default="Present")  # Present, Absent

    student = db.relationship("Student", back_populates="attendance_records")
    course = db.relationship("Course", back_populates="attendance_records")


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User")

    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at

    @staticmethod
    def create_for(user, expiry_minutes=30):
        token = PasswordResetToken(
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
        )
        return token


class Marks(db.Model):
    __tablename__ = "marks"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "semester", name="uq_marks_student_course_semester"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester = db.Column(db.String(40), nullable=False)
    assignment_marks = db.Column(db.Float, default=0)
    midterm_marks = db.Column(db.Float, default=0)
    final_marks = db.Column(db.Float, default=0)

    student = db.relationship("Student", back_populates="marks_records")
    course = db.relationship("Course", back_populates="marks_records")

    @property
    def total(self):
        return round((self.assignment_marks or 0) + (self.midterm_marks or 0) + (self.final_marks or 0), 2)

    @property
    def grade_and_points(self):
        return calculate_grade(self.total)

    @property
    def letter_grade(self):
        return self.grade_and_points[0]

    @property
    def gpa_points(self):
        return self.grade_and_points[1]


def calculate_grade(total):
    """Standard 4.0-scale grade mapping from a 0-100 total mark."""
    total = float(total or 0)
    if total >= 90:
        return ("A+", 4.00)
    if total >= 85:
        return ("A", 4.00)
    if total >= 80:
        return ("A-", 3.67)
    if total >= 75:
        return ("B+", 3.33)
    if total >= 70:
        return ("B", 3.00)
    if total >= 65:
        return ("B-", 2.67)
    if total >= 60:
        return ("C+", 2.33)
    if total >= 55:
        return ("C", 2.00)
    if total >= 50:
        return ("C-", 1.67)
    if total >= 45:
        return ("D", 1.00)
    return ("F", 0.00)
