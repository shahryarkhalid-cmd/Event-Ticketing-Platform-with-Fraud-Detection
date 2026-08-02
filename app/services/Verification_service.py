# services/verification_service.py
import random
from fastapi import HTTPException
from core.redis_client import redis_client
from services.send_email import send_verification_email
from models.Users import User
from sqlmodel import Session, select
OTP_EXPIRY_SECONDS = 600  # 10 minutes


def generate_and_send_otp(user_email: str):
    code = str(random.randint(100000, 999999))
    redis_key = f"email_verify:{user_email}"
    redis_client.setex(redis_key, OTP_EXPIRY_SECONDS, code)

    send_verification_email(user_email, code)

    return {"detail": "Verification code sent to your email"}


def verify_otp(email: str, submitted_code: str, session: Session):
    redis_key = f"email_verify:{email}"
    stored_code = redis_client.get(redis_key)

    if not stored_code:
        raise HTTPException(400, "Code expired or not found. Please request a new one.")

    if stored_code != submitted_code:
        raise HTTPException(400, "Incorrect verification code")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_verified = True
    session.add(user)
    session.commit()

    redis_client.delete(redis_key)

    return {"detail": "Email verified successfully. You can now log in."}