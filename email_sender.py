import smtplib
from email.mime.text import MIMEText
import os

def send_password_reset_email(email: str, code: str):
    """
    Sends a time-sensitive password reset code via SMTP email.
    Returns: (success: bool, error_message: str | None)
    """

    # 1. Load SMTP config – prefer Streamlit secrets if available
    try:
        import streamlit as st  # type: ignore
        from_addr = st.secrets.get("SMTP_USER")
        password = st.secrets.get("SMTP_PASS")
        smtp_host = st.secrets.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("SMTP_PORT", 465))
    except Exception:
        # Fallback to environment variables (e.g., local .env)
        from_addr = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASS")
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))

    to_addr = email

    # Debug line – visible in Cloud logs
    print(
        "DEBUG SMTP:",
        "from_addr=", from_addr,
        "host=", smtp_host,
        "port=", smtp_port,
        "pass_len=", len(password) if password else None,
    )

    if not from_addr or not password:
        return False, "SMTP credentials not configured"

    # 2. Build the email
    subject = "Your Reedz Password Reset Code"
    message = (
        f"Your Reedz password reset code is: {code}\n\n"
        "This code will expire in 5 minutes."
    )

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    # 3. Send via Gmail SMTP with SSL
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(from_addr, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        return True, None
    except Exception as e:
        # This is where `(334, b'UGFzc3dvcmQ6')` will surface
        print("SMTP ERROR:", repr(e))
        return False, f"Email failed: {e}"
