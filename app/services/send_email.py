# services/email_service.py
import os
import resend
resend.api_key = os.environ["RESEND_API_KEY"]

FROM_EMAIL = "onboarding@resend.dev"  # swap to your verified domain later, e.g. "noreply@yourapp.com"


def send_verification_email(to_email: str, code: str):
    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Verify your email",
            "html": f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
                    <h2>Verify your email</h2>
                    <p>Use the code below to verify your account:</p>
                    <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
                    <p>This code expires in 10 minutes.</p>
                </div>
            """,
        })
    except Exception as e:
        # Don't let a broken email service crash registration —
        # log it, but let the user request a resend afterward.
        print(f"Failed to send verification email to {to_email}: {e}")
        
        
def send_password_reset_email(to_email: str, code: str):
    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Reset your password",
            "html": f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
                    <h2>Reset your password</h2>
                    <p>Use the code below to reset your Tixora account password:</p>
                    <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
                    <p>This code expires in 10 minutes. If you didn't request this, you can ignore this email.</p>
                </div>
            """,
        })
    except Exception as e:
        print(f"Failed to send password reset email to {to_email}: {e}")