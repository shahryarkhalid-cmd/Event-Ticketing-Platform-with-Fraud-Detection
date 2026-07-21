from fastapi import FastAPI , Depends
import logging
from database import create_table
from sqlmodel import Session ,select
from database import get_session
from services.User_services import register_user , logging_in
from models.Users import UserCreate , UserLogin , User
from models.Event import EventCreate
from services.User_services import get_current_user
from services.Organizer_services import Make_Event , get_organizer_events
from fastapi.middleware.cors import CORSMiddleware
from dependencies.exception import Email_exist , User_Exist ,password_mismatch , Email_registration , email_existing , user_existence , incorrect_password , email_reg, forbidden , Forbidden
def lifespan(app : FastAPI):
    create_table()
    yield
    

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.add_exception_handler(Forbidden , forbidden)

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

@ app.post('/make_event')
def make_event(event : EventCreate , user : User = Depends(get_current_user) ,session : Session = Depends(get_session)):
    return Make_Event(event , user , session)
@ app.get('/get_all_events')
def get_all_event(user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
    return get_organizer_events(user , session)