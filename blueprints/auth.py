from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, PasswordResetToken
from blueprints.mailer import send_password_reset_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active_account():
            flash("This account has been deactivated. Contact the registrar.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"Welcome back, {username}.", "success")
        return redirect(url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        # Always show the same message whether or not the account exists,
        # so this form can't be used to check which usernames/emails are registered.
        generic_message = (
            "If an account with that username or email exists, "
            "a password reset link has been sent."
        )

        if user and user.is_active_account():
            reset_token = PasswordResetToken.create_for(
                user, expiry_minutes=current_app.config["RESET_TOKEN_EXPIRY_MINUTES"]
            )
            db.session.add(reset_token)
            db.session.commit()

            reset_url = url_for("auth.reset_password", token=reset_token.token, _external=True)
            send_password_reset_email(user.email, reset_url)

        flash(generic_message, "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    reset_token = PasswordResetToken.query.filter_by(token=token).first()

    if not reset_token or not reset_token.is_valid():
        flash("That reset link is invalid or has expired. Request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(new_password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_password.html", token=token)

        reset_token.user.set_password(new_password)
        reset_token.used = True
        db.session.commit()

        flash("Your password has been reset. Sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
