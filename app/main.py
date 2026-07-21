from fastapi import FastAPI , Depends
import logging
from database import create_table
from sqlmodel import Session ,select
from database import get_session
from services.User_services import register_user , logging_in
from models.Users import UserCreate , UserLogin
from dependencies.exception import Email_exist , User_Exist ,password_mismatch , Email_registration , email_existing , user_existence , incorrect_password , email_reg
def lifespan(app : FastAPI):
    create_table()
    yield
    

app = FastAPI(lifespan=lifespan)



logging.basicConfig(
    level = logging.INFO ,
    filename= "app.log" , 
    format= "%(asctime)s - %(levelname)s - %(message)s"
    )


# Adding Exceptions :
app.add_exception_handler(Email_exist , email_existing)
app.add_exception_handler(User_Exist , user_existence)
app.add_exception_handler(password_mismatch , incorrect_password)
app.add_exception_handler(Email_registration , email_reg)

logger = logging.getLogger(__name__)
# Health checking:
@app.get('/')
def health():
    logger.info('Home page')
    return {"message" : "Welcome to Event Ticketing System"}

# Health check:
@app.get("/health")
def health_check():
    logger.info('Health check')
    return {"status": "ok"}

# DB checking:
@app.get("/health/db")
def db_health_check(session: Session = Depends(get_session)):
    logging.info('Connected to DB')
    session.exec(select(1))
    return {"database": "connected"}

@ app.post('/auth/register')
def register(user : UserCreate , session : Session = Depends(get_session)):
    return register_user(user , session)

@ app.post('/auth/login')
def login(user : UserLogin , session : Session = Depends(get_session)):
    return logging_in(user , session)