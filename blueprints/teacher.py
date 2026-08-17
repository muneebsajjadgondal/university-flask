from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import TeacherCourse, Enrollment, Attendance, Marks, Student, User
from blueprints.utils import role_required

teacher_bp = Blueprint("teacher", __name__)


@teacher_bp.before_request
@login_required
@role_required("teacher")
def guard():
    pass


def get_own_assignment_or_404(assignment_id):
    assignment = db.session.get(TeacherCourse, assignment_id)
    if not assignment or assignment.teacher_id != current_user.teacher_profile.id:
        abort(404)
    return assignment


@teacher_bp.route("/")
def dashboard():
    teacher = current_user.teacher_profile
    assignments = TeacherCourse.query.filter_by(teacher_id=teacher.id).all()
    course_count = len({a.course_id for a in assignments})
    student_count = 0
    for a in assignments:
        student_count += Enrollment.query.filter_by(
            course_id=a.course_id, semester=a.semester, status="Active"
        ).count()
    return render_template(
        "teacher/dashboard.html", teacher=teacher, assignments=assignments,
        course_count=course_count, student_count=student_count,
    )


@teacher_bp.route("/courses")
def my_courses():
    teacher = current_user.teacher_profile
    assignments = TeacherCourse.query.filter_by(teacher_id=teacher.id).all()
    return render_template("teacher/my_courses.html", assignments=assignments)


@teacher_bp.route("/profile", methods=["GET", "POST"])
def profile():
    teacher = current_user.teacher_profile

    if request.method == "POST":
        teacher.phone = request.form.get("phone", "").strip() or None

        new_email = request.form.get("email", "").strip().lower()
        if new_email and new_email != current_user.email:
            if User.query.filter(User.email == new_email, User.id != current_user.id).first():
                flash("That email is already registered to another account.", "danger")
                return render_template("teacher/profile.html", teacher=teacher)
            current_user.email = new_email

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if new_password:
            if not current_password or not current_user.check_password(current_password):
                flash("Current password is incorrect. Password was not changed.", "danger")
                return render_template("teacher/profile.html", teacher=teacher)
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("teacher.profile"))

    return render_template("teacher/profile.html", teacher=teacher)


@teacher_bp.route("/courses/<int:assignment_id>/attendance", methods=["GET", "POST"])
def attendance(assignment_id):
    assignment = get_own_assignment_or_404(assignment_id)

    selected_date_str = request.values.get("date") or date.today().isoformat()
    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = date.today()

    enrolled = (
        Enrollment.query.filter_by(
            course_id=assignment.course_id, semester=assignment.semester, status="Active"
        ).all()
    )
    students = [e.student for e in enrolled]

    if request.method == "POST":
        for student in students:
            status = request.form.get(f"status_{student.id}", "Absent")
            record = Attendance.query.filter_by(
                student_id=student.id, course_id=assignment.course_id, date=selected_date
            ).first()
            if record:
                record.status = status
            else:
                db.session.add(Attendance(
                    student_id=student.id, course_id=assignment.course_id,
                    date=selected_date, status=status,
                ))
        db.session.commit()
        flash(f"Attendance saved for {selected_date.isoformat()}.", "success")
        return redirect(url_for("teacher.attendance", assignment_id=assignment.id, date=selected_date.isoformat()))

    existing = {
        r.student_id: r.status
        for r in Attendance.query.filter_by(course_id=assignment.course_id, date=selected_date).all()
    }

    return render_template(
        "teacher/attendance.html", assignment=assignment, students=students,
        selected_date=selected_date, existing=existing,
    )


@teacher_bp.route("/courses/<int:assignment_id>/marks", methods=["GET", "POST"])
def marks(assignment_id):
    assignment = get_own_assignment_or_404(assignment_id)

    enrolled = (
        Enrollment.query.filter_by(
            course_id=assignment.course_id, semester=assignment.semester, status="Active"
        ).all()
    )
    students = [e.student for e in enrolled]

    if request.method == "POST":
        for student in students:
            assignment_marks = request.form.get(f"assignment_{student.id}", "0") or "0"
            midterm_marks = request.form.get(f"midterm_{student.id}", "0") or "0"
            final_marks = request.form.get(f"final_{student.id}", "0") or "0"

            record = Marks.query.filter_by(
                student_id=student.id, course_id=assignment.course_id, semester=assignment.semester
            ).first()
            if not record:
                record = Marks(
                    student_id=student.id, course_id=assignment.course_id, semester=assignment.semester
                )
                db.session.add(record)

            try:
                record.assignment_marks = float(assignment_marks)
                record.midterm_marks = float(midterm_marks)
                record.final_marks = float(final_marks)
            except ValueError:
                flash(f"Invalid marks entered for {student.full_name}; skipped.", "warning")

        db.session.commit()
        flash("Marks saved.", "success")
        return redirect(url_for("teacher.marks", assignment_id=assignment.id))

    existing = {
        r.student_id: r
        for r in Marks.query.filter_by(course_id=assignment.course_id, semester=assignment.semester).all()
    }

    return render_template(
        "teacher/marks.html", assignment=assignment, students=students, existing=existing,
    )
