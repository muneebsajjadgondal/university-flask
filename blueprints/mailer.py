import smtplib
import ssl
from email.message import EmailMessage
from flask import current_app


def send_password_reset_email(to_email, reset_url):
    """Send a password reset link by email if SMTP is configured.

    If MAIL_SERVER isn't set (e.g. local development or a fresh deploy that
    hasn't configured email yet), the link is logged to the server console
    instead so the flow is still fully usable without any setup.
    """
    server = current_app.config.get("MAIL_SERVER")

    if not server:
        message = f"[password reset] no MAIL_SERVER configured — reset link for {to_email}: {reset_url}"
        current_app.logger.warning(message)
        print(message, flush=True)
        return False

    msg = EmailMessage()
    msg["Subject"] = "Reset your Registrar Portal password"
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to_email
    msg.set_content(
        "You requested a password reset for the University Registrar Portal.\n\n"
        f"Reset your password here: {reset_url}\n\n"
        "This link expires in 30 minutes. If you didn't request this, you can ignore this email."
    )

    port = current_app.config["MAIL_PORT"]
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = current_app.config.get("MAIL_USE_TLS", True)

    try:
        with smtplib.SMTP(server, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls(context=ssl.create_default_context())
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except Exception:
        current_app.logger.exception("Failed to send password reset email to %s", to_email)
        current_app.logger.info("Password reset link for %s: %s", to_email, reset_url)
        return False
