import os
from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from dotenv import load_dotenv

load_dotenv()

from config import Config
from extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.teacher import teacher_bp
    from blueprints.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        if current_user.role == "teacher":
            return redirect(url_for("teacher.dashboard"))
        return redirect(url_for("student.dashboard"))

    @app.context_processor
    def inject_globals():
        from datetime import date
        from markupsafe import Markup
        from flask_wtf.csrf import generate_csrf

        def csrf_token_field():
            return Markup(f'<input type="hidden" name="csrf_token" value="{generate_csrf()}">')

        return {"current_year": date.today().year, "csrf_token_field": csrf_token_field}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
