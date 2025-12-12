import smtplib
from email.mime.text import MIMEText
import os

def send_password_reset_email(email, code):
    """
    Sends a time-sensitive password reset code via SMTP email.
    Returns: (bool success, str error_message_or_None)
    """

    # 1. Try Streamlit secrets (Cloud)
    from_addr = None
    password = None
    smtp_host = "smtp.gmail.com"
    smtp_port = 465

    try:
        import streamlit as st
        from_addr = st.secrets.get("SMTP_USER")
        password = st.secrets.get("SMTP_PASS")
        smtp_host = st.secrets.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("SMTP_PORT", 465))
    except Exception:
        pass  # fallback below

    # 2. Fallback to env vars (local .env)
    if not from_addr:
        from_addr = os.getenv("SMTP_USER")
    if not password:
        password = os.getenv("SMTP_PASS")
    if not smtp_host:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    if not smtp_port:
        smtp_port = int(os.getenv("SMTP_PORT", "465"))

    to_addr = email

    print(
        "DEBUG SMTP:",
        "from_addr=", from_addr,
        "host=", smtp_host,
        "port=", smtp_port,
        "pass_len=", len(password) if password else None,
    )

    if not from_addr or not password:
        return False, "SMTP credentials not configured"

    subject = "Your Reedz Password Reset Code"
    message = f"Your Reedz password reset code is: {code}\n\nThis code will expire in 5 minutes."

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(from_addr, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        return True, None
    except Exception as e:
        print("SMTP ERROR:", repr(e))
        return False, f"Email failed: {e}"
