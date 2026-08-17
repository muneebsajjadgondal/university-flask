import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    _db_url = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
    # Render/Heroku-style URLs sometimes use postgres:// which SQLAlchemy 1.4+/2.x rejects
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    # Optional SMTP config for password-reset emails. If MAIL_SERVER is unset,
    # reset links are logged to the server console instead of emailed — this
    # keeps local/demo use working with zero setup. Set these env vars for
    # real email delivery in production.
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "registrar@university.edu")

    RESET_TOKEN_EXPIRY_MINUTES = 30
