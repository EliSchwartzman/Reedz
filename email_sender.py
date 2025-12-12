import smtplib                 # Standard library for SMTP email sending
from email.mime.text import MIMEText  # Constructs MIME-formatted email messages
import os                      # Access environment variables for SMTP credentials
import streamlit as st         # For st.secrets when running on Streamlit Cloud

def send_password_reset_email(email, code):
    """
    Sends a time-sensitive password reset code via SMTP email.

    Uses environment variables (local) or Streamlit secrets (cloud)
    for secure credential management.
    """

    # Prefer Streamlit secrets (cloud), fall back to env vars (local)
    from_addr = st.secrets.get("SMTP_USER") or os.getenv("SMTP_USER")
    password = st.secrets.get("SMTP_PASS") or os.getenv("SMTP_PASS")
    smtp_host = st.secrets.get("SMTP_HOST") or os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(st.secrets.get("SMTP_PORT") or os.getenv("SMTP_PORT", "465"))

    to_addr = email  # Destination email

    # Craft password reset email content
    subject = "Your Reedz Password Reset Code"
    message = f"Your Reedz password reset code is: {code}\n\nThis code will expire in 5 minutes."

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    try:
        # Establish SSL-encrypted SMTP connection
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            # Authenticate with SMTP server using credentials
            server.login(from_addr, password)
            # Send email (recipient as list for multiple addresses support)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        # Success
        return True, None
    except Exception as e:
        # Failure: surface SMTP/auth/network error back to caller
        return False, str(e)
