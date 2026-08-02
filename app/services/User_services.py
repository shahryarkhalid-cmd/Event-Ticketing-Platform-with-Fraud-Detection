from fastapi import Depends
from sqlmodel import Session , select
from database import get_session
import os
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError , jwt
from models.Users import User , UserCreate , UserLogin , RoleSelect , UserRole
from dependencies.hashing import hash_password , verify_password
from dependencies.exception import User_Exist , Email_exist , Email_registration , password_mismatch , Role_Already_Set , Invalid_Role_Selection
from dependencies.token import create_token
import logging
oauth_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
ALGORITHM = "HS256"
# Getting the current User Identity:
def get_current_user(token: str = Depends(oauth_scheme), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=[ALGORITHM])
        user_id = payload.get('sub')
        if user_id is None:
            raise HTTPException(status_code=401, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = session.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# Registring the User:
from services.Verification_service import generate_and_send_otp
def register_user(user : UserCreate , session : Session):
    hashed_pass = hash_password(user.password)
    final_user = User(full_name = user.full_name , hashed_password = hashed_pass , email=user.email)
    
    existing_email_user = session.exec(select(User).where(User.email == user.email)).first()
    
    if existing_email_user:
        logging.error('Email already exist')
        raise Email_exist()
    existing_user = session.exec(select(User).where(User.full_name == user.full_name)).first()
    
    if existing_user :
        logging.error('User already Exists')
        raise User_Exist()
    
    session.add(final_user)
    session.flush()         
    session.refresh(final_user)
    generate_and_send_otp(final_user.email)
    logging.info('User is added to DB')
    return {'message':'User added Sucessfully!'}



# Logging in the User:
from fastapi.security import OAuth2PasswordRequestForm
def logging_in(user: UserLogin, session: Session):

    user_email = session.exec(select(User).where(User.email == user.email)).first()
    if user_email is None:
        logging.error('Email is not registered!')
        raise Email_registration()

    verify = verify_password(user.password, user_email.hashed_password)
    if not verify:
        logging.error('Password MisMatching error')
        raise password_mismatch()

    if not user_email.is_verified:
        logging.warning(f"Unverified login attempt: {user_email.email}")
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    token = create_token({'sub': str(user_email.id)})
    logging.info("Token is created and logged in successful!")
    return {"access_token": token, "token_type": "bearer"}


# Returning the logged-in user's own profile (used by the frontend right
# after login/signup to decide whether to show the role-selection page
# or send the user straight to their dashboard):
def get_me(user1: User, session: Session):
    user = session.exec(select(User).where(User.id == user1.id)).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "role_selected": user.role_selected,
    }


# One-time role selection. Can only be called once per account - after
# that the role is locked and this will always raise Role_Already_Set.
def select_role(role_data: RoleSelect, user: User, session: Session):
    if user.role_selected:
        logging.error('Role already selected for this user')
        raise Role_Already_Set()

    if role_data.role not in (UserRole.customer, UserRole.organizer):
        logging.error('Invalid role selection attempted')
        raise Invalid_Role_Selection()

    user.role = role_data.role
    user.role_selected = True
    session.add(user)
    logging.info(f"Role '{role_data.role}' set for user {user.id}")
    return {"message": "Role set successfully", "role": user.role}


# services/user_service.py
import uuid
from fastapi import HTTPException
from core.supabase_client import supabase

PROFILE_BUCKET = "profile-pictures"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 3  # profile pics can be smaller than event banners

async def upload_profile_picture_service(file, current_user, session):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, or WEBP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {MAX_SIZE_MB}MB")

    ext = file.filename.split(".")[-1].lower()
    storage_path = f"{current_user.id}/{uuid.uuid4().hex}.{ext}"

    if current_user.profile_picture_storage_path:
        try:
            supabase.storage.from_(PROFILE_BUCKET).remove([current_user.profile_picture_storage_path])
        except Exception:
            pass

    supabase.storage.from_(PROFILE_BUCKET).upload(
        path=storage_path,
        file=contents,
        file_options={"content-type": file.content_type, "upsert": "true"},
    )
    picture_url = supabase.storage.from_(PROFILE_BUCKET).get_public_url(storage_path)

    current_user.profile_picture_url = picture_url
    current_user.profile_picture_storage_path = storage_path
    session.add(current_user)
    session.flush()
    session.refresh(current_user)

    return {"profile_picture_url": picture_url}


# services/user_service.py
from datetime import datetime , timezone
from models.Users import UserUpdate
def update_user_profile_service(update_data: UserUpdate, current_user: User, session: Session):
    update_fields = update_data.model_dump(exclude_unset=True)  # only fields actually sent

    for field, value in update_fields.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.flush()
    session.refresh(current_user)

    return current_user


# Updating the password:
from models.Users import PasswordChange
def change_password(password_data: PasswordChange, user: User, session: Session):
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    user.hashed_password = hash_password(password_data.new_password)
    session.add(user)
    session.flush()
    return {"message": "Password updated successfully"}


