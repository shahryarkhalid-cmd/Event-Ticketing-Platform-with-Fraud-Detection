from fastapi import FastAPI , Depends
import logging
from database import create_table
from sqlmodel import Session ,select
from database import get_session
from services.User_services import register_user , logging_in
from models.Users import UserCreate , UserLogin , User
from models.Event import EventCreateWithTiers
from services.User_services import get_current_user
from services.Organizer_services import Make_Event , get_organizer_events , delete_organizer_event , delete_all_organizer_event , get_specific_event , add_ticket_tiers , List_Tickets
from fastapi.middleware.cors import CORSMiddleware
from models.Event import EventRead
from dependencies.exception import (Email_exist , User_Exist ,password_mismatch , Email_registration , email_existing , user_existence , 
            incorrect_password , email_reg, forbidden , Forbidden , Event_Not_Found , event_not_found , 
            Not_customer , not_customer , Ticket_Tier_not_found , no_ticket_tier ,Order_Quantity_Error , less_order_quantity , 
            Not_Enough_Tickets , not_enough_tickets , booking_contention , BookingContention)
from models.Ticket import TicketTierRead
from typing import Optional 
from fastapi import Query
from typing import List
from models.Orders import OrderCreate , OrderRead
from services.Order_services import get_my_orders , book_ticket
from services.Customer_services import search_events_customer
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
app.add_exception_handler(Event_Not_Found , event_not_found)
app.add_exception_handler(Not_customer , not_customer)
app.add_exception_handler(Ticket_Tier_not_found , no_ticket_tier)
app.add_exception_handler(Order_Quantity_Error , less_order_quantity)
app.add_exception_handler(Not_Enough_Tickets , not_enough_tickets)
app.add_exception_handler(BookingContention , booking_contention)
logger = logging.getLogger(__name__)
# Health checking and home page:
@app.get('/')
def home():
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

@app.post("/publish-event")
def publish_event_route(
    event_data: EventCreateWithTiers,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return Make_Event(event_data, user, session)


@ app.get('/get_all_events')
def get_all_event(user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
    return get_organizer_events(user , session)

@ app.get('/get_event/{id}')
def get_event(id : int , user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
    return get_specific_event(id , user , session)

@ app.delete('/delete_event/{id}')
def delete_event(id : int , user : User = Depends(get_current_user), session : Session = Depends(get_session)):
    return delete_organizer_event(id , user , session)

@ app.delete('/delete_all_event')
def delete_all_event(user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
    return delete_all_organizer_event(user , session)


@app.get("/events/{event_id}/ticket-tiers", response_model=List[TicketTierRead])
def list_ticket_tiers(event_id: int,user : User = Depends(get_current_user),  session: Session = Depends(get_session)):
    return List_Tickets(event_id ,user ,  session)


# Customer Session: 
@app.get("/events/customer", response_model=List[EventRead])
def search_events(
    session: Session = Depends(get_session),
    search: Optional[str] = Query(None, description="Search by event name"),
    venue: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    return search_events_customer(session, search, venue, city, country, category)

# placing the order :
@app.post("/orders", response_model=OrderRead)
def create_order(
    order_data: OrderCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return book_ticket(order_data, user, session)


@app.get("/orders/me", response_model=List[OrderRead])
def my_orders(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_my_orders(user, session)
