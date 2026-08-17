from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import (
    Department, User, Teacher, Student, Course, TeacherCourse, Enrollment, Attendance, Marks
)
from blueprints.utils import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
@login_required
@role_required("admin")
def guard():
    pass


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


# ---------- Dashboard ----------

@admin_bp.route("/")
def dashboard():
    stats = {
        "students": Student.query.count(),
        "teachers": Teacher.query.count(),
        "courses": Course.query.count(),
        "departments": Department.query.count(),
        "active_enrollments": Enrollment.query.filter_by(status="Active").count(),
    }
    recent = (
        Enrollment.query.order_by(Enrollment.enrolled_at.desc()).limit(6).all()
    )
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


# ---------- My Profile ----------

@admin_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        new_email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        if new_email and new_email != current_user.email:
            if User.query.filter(User.email == new_email, User.id != current_user.id).first():
                flash("That email is already registered to another account.", "danger")
                return render_template("admin/profile.html")
            current_user.email = new_email

        if new_password:
            if not current_password or not current_user.check_password(current_password):
                flash("Current password is incorrect. Password was not changed.", "danger")
                return render_template("admin/profile.html")
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("admin.profile"))

    return render_template("admin/profile.html")


# ---------- Departments ----------

@admin_bp.route("/departments")
def departments_list():
    rows = Department.query.order_by(Department.name).all()
    return render_template("admin/departments/list.html", rows=rows)


@admin_bp.route("/departments/new", methods=["GET", "POST"])
def departments_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip().upper()
        building = request.form.get("building", "").strip() or None

        if not name or not code:
            flash("Name and code are required.", "danger")
            return render_template("admin/departments/form.html", dept=None)

        if Department.query.filter((Department.name == name) | (Department.code == code)).first():
            flash("A department with that name or code already exists.", "danger")
            return render_template("admin/departments/form.html", dept=None)

        db.session.add(Department(name=name, code=code, building=building))
        db.session.commit()
        flash("Department created.", "success")
        return redirect(url_for("admin.departments_list"))

    return render_template("admin/departments/form.html", dept=None)


@admin_bp.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"])
def departments_edit(dept_id):
    dept = db.session.get(Department, dept_id) or abort(404)

    if request.method == "POST":
        dept.name = request.form.get("name", "").strip()
        dept.code = request.form.get("code", "").strip().upper()
        dept.building = request.form.get("building", "").strip() or None

        if not dept.name or not dept.code:
            flash("Name and code are required.", "danger")
            return render_template("admin/departments/form.html", dept=dept)

        db.session.commit()
        flash("Department updated.", "success")
        return redirect(url_for("admin.departments_list"))

    return render_template("admin/departments/form.html", dept=dept)


@admin_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
def departments_delete(dept_id):
    dept = db.session.get(Department, dept_id) or abort(404)
    db.session.delete(dept)
    db.session.commit()
    flash("Department deleted.", "info")
    return redirect(url_for("admin.departments_list"))


# ---------- Teachers ----------

@admin_bp.route("/teachers")
def teachers_list():
    rows = Teacher.query.order_by(Teacher.full_name).all()
    return render_template("admin/teachers/list.html", rows=rows)


@admin_bp.route("/teachers/new", methods=["GET", "POST"])
def teachers_new():
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip() or None
        title = request.form.get("title", "").strip() or "Lecturer"
        department_id = request.form.get("department_id") or None
        hire_date = parse_date(request.form.get("hire_date"))

        errors = []
        if not full_name or not username or not email or not password:
            errors.append("Name, username, email, and password are required.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("That email is already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/teachers/form.html", teacher=None, departments=departments)

        user = User(username=username, email=email, role="teacher", status="active")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        teacher = Teacher(
            user_id=user.id, full_name=full_name, phone=phone, title=title,
            department_id=department_id, hire_date=hire_date,
        )
        db.session.add(teacher)
        db.session.commit()
        flash("Instructor created.", "success")
        return redirect(url_for("admin.teachers_list"))

    return render_template("admin/teachers/form.html", teacher=None, departments=departments)


@admin_bp.route("/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
def teachers_edit(teacher_id):
    teacher = db.session.get(Teacher, teacher_id) or abort(404)
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        teacher.full_name = request.form.get("full_name", "").strip()
        teacher.phone = request.form.get("phone", "").strip() or None
        teacher.title = request.form.get("title", "").strip() or "Lecturer"
        teacher.department_id = request.form.get("department_id") or None
        teacher.hire_date = parse_date(request.form.get("hire_date"))

        new_email = request.form.get("email", "").strip().lower()
        if new_email and new_email != teacher.user.email:
            if User.query.filter(User.email == new_email, User.id != teacher.user_id).first():
                flash("That email is already registered to another account.", "danger")
                return render_template("admin/teachers/form.html", teacher=teacher, departments=departments)
            teacher.user.email = new_email

        new_password = request.form.get("password", "")
        if new_password:
            teacher.user.set_password(new_password)

        if not teacher.full_name:
            flash("Name is required.", "danger")
            return render_template("admin/teachers/form.html", teacher=teacher, departments=departments)

        db.session.commit()
        flash("Instructor updated.", "success")
        return redirect(url_for("admin.teachers_list"))

    return render_template("admin/teachers/form.html", teacher=teacher, departments=departments)


@admin_bp.route("/teachers/<int:teacher_id>/delete", methods=["POST"])
def teachers_delete(teacher_id):
    teacher = db.session.get(Teacher, teacher_id) or abort(404)
    user = teacher.user
    db.session.delete(user)  # cascades to teacher profile
    db.session.commit()
    flash("Instructor deleted.", "info")
    return redirect(url_for("admin.teachers_list"))


# ---------- Students ----------

@admin_bp.route("/students")
def students_list():
    rows = Student.query.order_by(Student.roll_number).all()
    return render_template("admin/students/list.html", rows=rows)


@admin_bp.route("/students/new", methods=["GET", "POST"])
def students_new():
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip() or None
        gender = request.form.get("gender", "Other")
        dob = parse_date(request.form.get("date_of_birth"))
        department_id = request.form.get("department_id") or None
        enrollment_year = request.form.get("enrollment_year") or None
        current_semester = request.form.get("current_semester") or 1

        errors = []
        if not roll_number or not full_name or not username or not email or not password:
            errors.append("Roll number, name, username, email, and password are required.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("That email is already registered.")
        if Student.query.filter_by(roll_number=roll_number).first():
            errors.append("That roll number is already in use.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/students/form.html", student=None, departments=departments)

        user = User(username=username, email=email, role="student", status="active")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        student = Student(
            user_id=user.id, roll_number=roll_number, full_name=full_name, email=email,
            phone=phone, gender=gender, date_of_birth=dob, department_id=department_id,
            enrollment_year=enrollment_year, current_semester=current_semester, status="active",
        )
        db.session.add(student)
        db.session.commit()
        flash("Student created.", "success")
        return redirect(url_for("admin.students_list"))

    return render_template("admin/students/form.html", student=None, departments=departments)


@admin_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def students_edit(student_id):
    student = db.session.get(Student, student_id) or abort(404)
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()
        if roll_number != student.roll_number and Student.query.filter_by(roll_number=roll_number).first():
            flash("That roll number is already in use.", "danger")
            return render_template("admin/students/form.html", student=student, departments=departments)

        student.roll_number = roll_number
        student.full_name = request.form.get("full_name", "").strip()
        student.phone = request.form.get("phone", "").strip() or None
        student.gender = request.form.get("gender", "Other")
        student.date_of_birth = parse_date(request.form.get("date_of_birth"))
        student.department_id = request.form.get("department_id") or None
        student.enrollment_year = request.form.get("enrollment_year") or None
        student.current_semester = request.form.get("current_semester") or 1
        student.status = request.form.get("status", "active")

        new_email = request.form.get("email", "").strip().lower()
        if new_email and new_email != student.user.email:
            if User.query.filter(User.email == new_email, User.id != student.user_id).first():
                flash("That email is already registered to another account.", "danger")
                return render_template("admin/students/form.html", student=student, departments=departments)
            student.user.email = new_email
            student.email = new_email

        new_password = request.form.get("password", "")
        if new_password:
            student.user.set_password(new_password)

        if not student.full_name or not student.roll_number:
            flash("Roll number and name are required.", "danger")
            return render_template("admin/students/form.html", student=student, departments=departments)

        db.session.commit()
        flash("Student updated.", "success")
        return redirect(url_for("admin.students_list"))

    return render_template("admin/students/form.html", student=student, departments=departments)


@admin_bp.route("/students/<int:student_id>/delete", methods=["POST"])
def students_delete(student_id):
    student = db.session.get(Student, student_id) or abort(404)
    user = student.user
    db.session.delete(user)  # cascades to student profile, enrollments, attendance, marks
    db.session.commit()
    flash("Student deleted.", "info")
    return redirect(url_for("admin.students_list"))


# ---------- Courses ----------

@admin_bp.route("/courses")
def courses_list():
    rows = Course.query.order_by(Course.code).all()
    return render_template("admin/courses/list.html", rows=rows)


@admin_bp.route("/courses/new", methods=["GET", "POST"])
def courses_new():
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        title = request.form.get("title", "").strip()
        credit_hours = request.form.get("credit_hours") or 3
        department_id = request.form.get("department_id") or None
        capacity = request.form.get("capacity") or 40

        if not code or not title:
            flash("Code and title are required.", "danger")
            return render_template("admin/courses/form.html", course=None, departments=departments)

        if Course.query.filter_by(code=code).first():
            flash("A course with that code already exists.", "danger")
            return render_template("admin/courses/form.html", course=None, departments=departments)

        db.session.add(Course(
            code=code, title=title, credit_hours=credit_hours,
            department_id=department_id, capacity=capacity,
        ))
        db.session.commit()
        flash("Course created.", "success")
        return redirect(url_for("admin.courses_list"))

    return render_template("admin/courses/form.html", course=None, departments=departments)


@admin_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
def courses_edit(course_id):
    course = db.session.get(Course, course_id) or abort(404)
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        new_code = request.form.get("code", "").strip().upper()
        if new_code != course.code and Course.query.filter_by(code=new_code).first():
            flash("A course with that code already exists.", "danger")
            return render_template("admin/courses/form.html", course=course, departments=departments)

        course.code = new_code
        course.title = request.form.get("title", "").strip()
        course.credit_hours = request.form.get("credit_hours") or 3
        course.department_id = request.form.get("department_id") or None
        course.capacity = request.form.get("capacity") or 40

        if not course.code or not course.title:
            flash("Code and title are required.", "danger")
            return render_template("admin/courses/form.html", course=course, departments=departments)

        db.session.commit()
        flash("Course updated.", "success")
        return redirect(url_for("admin.courses_list"))

    return render_template("admin/courses/form.html", course=course, departments=departments)


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
def courses_delete(course_id):
    course = db.session.get(Course, course_id) or abort(404)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.courses_list"))


# ---------- Course <-> Teacher assignments ----------

@admin_bp.route("/courses/<int:course_id>/assignments", methods=["GET", "POST"])
def course_assignments(course_id):
    course = db.session.get(Course, course_id) or abort(404)
    teachers = Teacher.query.order_by(Teacher.full_name).all()

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id")
        semester = request.form.get("semester", "").strip()

        if not teacher_id or not semester:
            flash("Instructor and semester are required.", "danger")
        elif TeacherCourse.query.filter_by(
            teacher_id=teacher_id, course_id=course.id, semester=semester
        ).first():
            flash("That instructor is already assigned to this course for that semester.", "danger")
        else:
            db.session.add(TeacherCourse(teacher_id=teacher_id, course_id=course.id, semester=semester))
            db.session.commit()
            flash("Instructor assigned.", "success")
        return redirect(url_for("admin.course_assignments", course_id=course.id))

    return render_template("admin/courses/assignments.html", course=course, teachers=teachers)


@admin_bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
def assignment_delete(assignment_id):
    assignment = db.session.get(TeacherCourse, assignment_id) or abort(404)
    course_id = assignment.course_id
    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment removed.", "info")
    return redirect(url_for("admin.course_assignments", course_id=course_id))


# ---------- Enrollments ----------

@admin_bp.route("/enrollments")
def enrollments_list():
    rows = Enrollment.query.order_by(Enrollment.enrolled_at.desc()).all()
    return render_template("admin/enrollments/list.html", rows=rows)


@admin_bp.route("/enrollments/new", methods=["GET", "POST"])
def enrollments_new():
    students = Student.query.order_by(Student.roll_number).all()
    courses = Course.query.order_by(Course.code).all()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        course_id = request.form.get("course_id")
        semester = request.form.get("semester", "").strip()
        status = request.form.get("status", "Active")

        if not student_id or not course_id or not semester:
            flash("Student, course, and semester are required.", "danger")
            return render_template("admin/enrollments/form.html", enrollment=None, students=students, courses=courses)

        if Enrollment.query.filter_by(student_id=student_id, course_id=course_id, semester=semester).first():
            flash("This student is already enrolled in that course for that semester.", "danger")
            return render_template("admin/enrollments/form.html", enrollment=None, students=students, courses=courses)

        db.session.add(Enrollment(student_id=student_id, course_id=course_id, semester=semester, status=status))
        db.session.commit()
        flash("Enrollment created.", "success")
        return redirect(url_for("admin.enrollments_list"))

    return render_template("admin/enrollments/form.html", enrollment=None, students=students, courses=courses)


@admin_bp.route("/enrollments/<int:enrollment_id>/edit", methods=["GET", "POST"])
def enrollments_edit(enrollment_id):
    enrollment = db.session.get(Enrollment, enrollment_id) or abort(404)
    students = Student.query.order_by(Student.roll_number).all()
    courses = Course.query.order_by(Course.code).all()

    if request.method == "POST":
        enrollment.student_id = request.form.get("student_id")
        enrollment.course_id = request.form.get("course_id")
        enrollment.semester = request.form.get("semester", "").strip()
        enrollment.status = request.form.get("status", "Active")

        if not enrollment.semester:
            flash("Semester is required.", "danger")
            return render_template("admin/enrollments/form.html", enrollment=enrollment, students=students, courses=courses)

        db.session.commit()
        flash("Enrollment updated.", "success")
        return redirect(url_for("admin.enrollments_list"))

    return render_template("admin/enrollments/form.html", enrollment=enrollment, students=students, courses=courses)


@admin_bp.route("/enrollments/<int:enrollment_id>/delete", methods=["POST"])
def enrollments_delete(enrollment_id):
    enrollment = db.session.get(Enrollment, enrollment_id) or abort(404)
    db.session.delete(enrollment)
    db.session.commit()
    flash("Enrollment deleted.", "info")
    return redirect(url_for("admin.enrollments_list"))


# ---------- Administrators ----------

@admin_bp.route("/admins")
def admins_list():
    rows = User.query.filter_by(role="admin").order_by(User.username).all()
    return render_template("admin/admins/list.html", rows=rows)


@admin_bp.route("/admins/new", methods=["GET", "POST"])
def admins_new():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = []
        if not username or not email or not password:
            errors.append("Username, email, and password are required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("That email is already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/admins/form.html")

        new_admin = User(username=username, email=email, role="admin", status="active")
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        flash("Administrator created.", "success")
        return redirect(url_for("admin.admins_list"))

    return render_template("admin/admins/form.html")


@admin_bp.route("/admins/<int:user_id>/delete", methods=["POST"])
def admins_delete(user_id):
    target = db.session.get(User, user_id) or abort(404)

    if target.id == current_user.id:
        flash("You can't delete your own account. Ask another administrator to do it.", "danger")
        return redirect(url_for("admin.admins_list"))

    admin_count = User.query.filter_by(role="admin").count()
    if admin_count <= 1:
        flash("You can't delete the last remaining administrator account.", "danger")
        return redirect(url_for("admin.admins_list"))

    db.session.delete(target)
    db.session.commit()
    flash("Administrator deleted.", "info")
    return redirect(url_for("admin.admins_list"))
