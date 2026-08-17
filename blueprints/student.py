from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Enrollment, Attendance, Marks, calculate_grade
from blueprints.utils import role_required

student_bp = Blueprint("student", __name__)


@student_bp.before_request
@login_required
@role_required("student")
def guard():
    pass


@student_bp.route("/")
def dashboard():
    student = current_user.student_profile
    active_enrollments = Enrollment.query.filter_by(student_id=student.id, status="Active").count()
    marks_records = Marks.query.filter_by(student_id=student.id).all()
    cgpa = _compute_cgpa(marks_records)
    return render_template(
        "student/dashboard.html", student=student,
        active_enrollments=active_enrollments, cgpa=cgpa,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    student = current_user.student_profile

    if request.method == "POST":
        student.phone = request.form.get("phone", "").strip() or None

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if new_password:
            if not current_password or not current_user.check_password(current_password):
                flash("Current password is incorrect. Password was not changed.", "danger")
                return render_template("student/profile.html", student=student)
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student)


@student_bp.route("/enrollments")
def enrollments():
    student = current_user.student_profile
    rows = Enrollment.query.filter_by(student_id=student.id).order_by(Enrollment.semester.desc()).all()
    return render_template("student/enrollments.html", rows=rows)


@student_bp.route("/attendance")
def attendance():
    student = current_user.student_profile
    rows = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()

    by_course = {}
    for r in rows:
        by_course.setdefault(r.course_id, {"course": r.course, "present": 0, "total": 0})
        by_course[r.course_id]["total"] += 1
        if r.status == "Present":
            by_course[r.course_id]["present"] += 1

    summary = list(by_course.values())
    for s in summary:
        s["percent"] = round((s["present"] / s["total"]) * 100, 1) if s["total"] else 0

    return render_template("student/attendance.html", rows=rows, summary=summary)


def _compute_cgpa(marks_records):
    if not marks_records:
        return None
    total_points = sum(m.gpa_points * m.course.credit_hours for m in marks_records if m.course)
    total_credits = sum(m.course.credit_hours for m in marks_records if m.course)
    if not total_credits:
        return None
    return round(total_points / total_credits, 2)


@student_bp.route("/grades")
def grades():
    student = current_user.student_profile
    rows = Marks.query.filter_by(student_id=student.id).all()
    cgpa = _compute_cgpa(rows)
    return render_template("student/grades.html", rows=rows, cgpa=cgpa)
