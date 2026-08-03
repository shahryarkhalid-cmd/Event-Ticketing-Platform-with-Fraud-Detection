from dotenv import load_dotenv
load_dotenv()
import os
import smtplib
from email.mime.text import MIMEText

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]


def _send_email(to_email: str, subject: str, html_body: str):
    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [to_email], msg.as_string())
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


def send_verification_email(to_email: str, code: str):
    _send_email(to_email, "Verify your email", f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
            <h2>Verify your email</h2>
            <p>Use the code below to verify your account:</p>
            <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
            <p>This code expires in 10 minutes.</p>
        </div>
    """)


def send_password_reset_email(to_email: str, code: str):
    _send_email(to_email, "Reset your password", f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
            <h2>Reset your password</h2>
            <p>Use the code below to reset your account password:</p>
            <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
            <p>This code expires in 10 minutes. If you didn't request this, ignore this email.</p>
        </div>
    """)