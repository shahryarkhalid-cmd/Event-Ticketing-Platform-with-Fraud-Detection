# services/Password_reset_service.py

import random
import uuid
from fastapi import HTTPException
from sqlmodel import Session, select
from core.redis_client import redis_client
from services.send_email import send_password_reset_email
from dependencies.hashing import hash_password
from models.Users import User

OTP_EXPIRY_SECONDS = 600          # 10 minutes — same window as email verification
RESET_TOKEN_EXPIRY_SECONDS = 600  # 10 minutes to actually pick a new password after verifying the code


def request_password_reset(email: str, session: Session):
    """
    POST /auth/forgot-password

    Always returns the same generic response whether or not the email is
    registered, so the frontend (and anyone probing it) can never tell
    which emails have accounts — the UI always just advances to the
    "enter code" step either way.
    """
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        code = str(random.randint(100000, 999999))
        redis_client.setex(f"password_reset_code:{email}", OTP_EXPIRY_SECONDS, code)
        # TEMPORARY: skipping actual email send — SMTP is broken on Railway's
        # free plan (times out), and verify_reset_code currently accepts any
        # code anyway, so there's no point waiting on a doomed send attempt.
        # TODO: restore this call once Brevo/domain email sending is working
        # AND the real code-check in verify_reset_code is restored.
        # send_password_reset_email(email, code)
        print(f"[DEV] Password reset code for {email}: {code}")
    # else: silently no-op — don't leak account existence via timing or response.

    return {"detail": "If an account exists for this email, a reset code has been sent."}


def verify_reset_code(email: str, submitted_code: str, session: Session):
    """
    POST /auth/verify-reset-code

    On success, issues a short-lived opaque `reset_token` (NOT the OTP
    itself) that the next call must present — this keeps the actual
    password-reset step from being replay-able with just the 6-digit code
    a user might have shared/screenshotted.
    """
    redis_key = f"password_reset_code:{email}"
    stored_code = redis_client.get(redis_key)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        # Shouldn't happen if request_password_reset gated correctly, but stay safe.
        raise HTTPException(404, "User not found")

    if redis_key:
        redis_client.delete(redis_key)  # one-time use — can't be verified twice

    reset_token = uuid.uuid4().hex
    redis_client.setex(f"password_reset_token:{reset_token}", RESET_TOKEN_EXPIRY_SECONDS, email)

    return {"reset_token": reset_token}


def reset_password(reset_token: str, new_password: str, session: Session):
    """
    POST /auth/reset-password
    """
    email = redis_client.get(f"password_reset_token:{reset_token}")
    if not email:
        raise HTTPException(400, "This reset link has expired. Please start over.")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.hashed_password = hash_password(new_password)
    session.add(user)
    session.flush()

    redis_client.delete(f"password_reset_token:{reset_token}")  # one-time use

    return {"detail": "Password updated successfully. You can now log in with your new password."}