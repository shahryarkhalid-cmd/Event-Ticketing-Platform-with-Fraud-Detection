from fastapi import Depends
from sqlmodel import Session , select
from database import get_session
import os
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError , jwt
from models.Users import User , UserCreate , UserLogin
from dependencies.hashing import hash_password , verify_password
from dependencies.exception import User_Exist , Email_exist , Email_registration , password_mismatch
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
    logging.info('User is added to DB')
    return {'message':'User added Sucessfully!'}



# Logging in the User:
from fastapi.security import OAuth2PasswordRequestForm
def logging_in(user : OAuth2PasswordRequestForm , session : Session):
    
    # verfiying:
    user_email = session.exec(select(User).where(User.email == user.username)).first()
    if user_email is None:
        logging.error('Email is not registered!')
        raise Email_registration()
    verify = verify_password(user.password , user_email.hashed_password)
    
    if not verify:
        logging.error('Password MisMatching error')
        raise password_mismatch()
    token = create_token({'sub' : str(user_email.id)})
    logging.info("Token is created and logged in sucessful!")
    return {"access_token": token, "token_type": "bearer"}