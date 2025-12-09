import smtplib  # Standard library for SMTP email sending
from email.mime.text import MIMEText  # Constructs MIME-formatted email messages
import os  # Access environment variables for SMTP credentials


def send_password_reset_email(email, code):
    """
    Sends a time-sensitive password reset code via SMTP email.
    
    Uses environment variables for secure credential management.
    
    Args:
        email (str): Recipient's email address. Must be @gmail, @terpmail, @umd.edu, or other gmail derivative.
        code (str): Temporary reset code (expires in 5 minutes).
    
    Returns:
        tuple: (bool success, str error_message_or_None)
    """
    # Load SMTP (Simple Mail Transfer Protocol) configuration from environment variables
    from_addr = os.getenv("SMTP_USER")  # Sender email address
    password = os.getenv("SMTP_PASS")   # Sender email password/app token
    smtp_host = os.getenv("SMTP_HOST")  # SMTP server hostname (e.g., 'smtp.gmail.com')
    smtp_port = int(os.getenv("SMTP_PORT", "465"))  # SSL port (default 465)
    
    to_addr = email  # Destination email (any valid address accepted)
    
    # Craft password reset email content
    subject = "Your Reedz Password Reset Code"
    message = f"Your Reedz password reset code is: {code}\n\nThis code will expire in 5 minutes."
    
    # Create MIME message object for proper email formatting
    msg = MIMEText(message)
    msg["Subject"] = subject      # Email subject line
    msg["From"] = from_addr       # Sender address in headers
    msg["To"] = to_addr           # Recipient address in headers
    
    # Attempt secure SMTP transmission with SSL (Secure Sockets Layer)
    try:
        # Establish SSL-encrypted SMTP connection
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            # Authenticate with SMTP server using credentials
            server.login(from_addr, password)
            # Send email (recipient as list for multiple addresses support)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        # Success: return True with no error
        return True, None
        
    # Catch all SMTP/auth/network errors
    except Exception as e:
        # Failure: return False with error details for debugging
        return False, str(e)
