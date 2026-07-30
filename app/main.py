from fastapi import FastAPI , Depends
import logging
from database import create_table
from sqlmodel import Session ,select
from database import get_session
from services.User_services import register_user , logging_in
from models.Users import UserCreate , UserLogin , User , RoleSelect , UserRead
from models.Event import EventCreateWithTiers
from services.User_services import get_current_user , get_me , select_role
from services.Organizer_services import Make_Event , get_organizer_events , delete_organizer_event , delete_all_organizer_event , get_specific_event , List_Tickets , get_analytics_summary , get_popular_ticket_categories , get_ticket_sales_last_7_days , refund_order , get_monthly_revenue_trend , get_revenue_overview ,get_organizer_all_bookings  , get_fraud_orders
from fastapi.middleware.cors import CORSMiddleware
from models.Event import EventRead
from dependencies.exception import (Email_exist , User_Exist ,password_mismatch , Email_registration , email_existing , user_existence , 
            incorrect_password , email_reg, forbidden , Forbidden , Event_Not_Found , event_not_found , 
            Not_customer , not_customer , Ticket_Tier_not_found , no_ticket_tier ,Order_Quantity_Error , less_order_quantity , 
            Not_Enough_Tickets , not_enough_tickets , booking_contention , BookingContention ,
            not_order , Not_Order , order_mismatch , paid_refund , Paid_Refund ,
            Order_Mismatch , not_pending_order ,
            Not_Pending_Order , not_your_event , Not_Your_Event 
            , invalid_webhook_payload_handler , invalid_webhook_signature_handler ,InvalidWebhookPayload ,InvalidWebhookSignature
            , Role_Already_Set , Invalid_Role_Selection , role_already_set , invalid_role_selection , Not_Your_Ticket , Ticket_Not_Found
            , not_your_ticket , ticket_not_found)
from models.Ticket import TicketTierRead
from typing import Optional 
from fastapi import Query
from typing import List
from models.Orders import OrderCreate , OrderRead
from services.Order_services import get_my_orders , book_ticket
from services.Customer_services import search_events_customer
from services.Payment_services import create_checkout_session
from services.Customer_services import get_public_event_detail


# Adding API Scheduling:
from apscheduler.schedulers.background import BackgroundScheduler
from database import engine  # your existing SQLAlchemy engine
from sqlmodel import Session
from services.order_expiry import expire_stale_orders

def run_expiry_job():
    with Session(engine) as session:
        count = expire_stale_orders(session)
        if count:
            logging.info(f"Expired {count} stale pending orders")

scheduler = BackgroundScheduler()
scheduler.add_job(run_expiry_job, "interval", minutes=10)


# ===========================================================================================

def lifespan(app: FastAPI):
    create_table()
    scheduler.start()
    yield
    scheduler.shutdown()
    

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
app.add_exception_handler(Not_Order , not_order)
app.add_exception_handler(Order_Mismatch , order_mismatch )
app.add_exception_handler(Not_Pending_Order , not_pending_order)
app.add_exception_handler(Not_Your_Event , not_your_event)
app.add_exception_handler(Paid_Refund , paid_refund)
app.add_exception_handler(InvalidWebhookSignature , invalid_webhook_signature_handler)
app.add_exception_handler(InvalidWebhookPayload , invalid_webhook_payload_handler)
app.add_exception_handler(Role_Already_Set , role_already_set)
app.add_exception_handler(Invalid_Role_Selection , invalid_role_selection)
app.add_exception_handler(Not_Your_Ticket , not_your_ticket)
app.add_exception_handler(Ticket_Not_Found , ticket_not_found)

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
from fastapi.security import OAuth2PasswordRequestForm

'''@ app.post('/auth/login')
def login(user : OAuth2PasswordRequestForm = Depends() , session : Session = Depends(get_session)):
    return logging_in(user , session)'''

@ app.post('/auth/login')
def login(user : UserLogin , session : Session = Depends(get_session)):
    return logging_in(user , session)

# Returns the logged-in user's profile, including whether they have
# already picked a role. The frontend calls this right after login/signup
# to decide: role-selection page (first time) vs. straight to dashboard.
@app.get('/users/me', response_model=UserRead)
def read_current_user(user: User = Depends(get_current_user)):
    return get_me(user)

# One-time role selection (customer or organizer). Locked after first use.
@app.post('/auth/select-role')
def choose_role(
    role_data: RoleSelect,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return select_role(role_data, user, session)

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

# Organizer Dashboard:

@app.get("/organizer/analytics/summary")
def analytics_summary(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_analytics_summary(user, session)

@app.get("/organizer/analytics/ticket-sales")
def ticket_sales(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_ticket_sales_last_7_days(user, session)

@app.get("/organizer/analytics/popular-categories")
def popular_categories(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_popular_ticket_categories(user, session)

@app.get("/organizer/bookings")
def all_bookings(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_organizer_all_bookings(user, session)

@app.get("/organizer/revenue/overview")
def revenue_overview(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_revenue_overview(user, session)

@app.get("/organizer/revenue/trend")
def revenue_trend(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_monthly_revenue_trend(user, session)

@app.post("/organizer/orders/{order_id}/refund")
def refund(
    order_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return refund_order(order_id, user, session)

from models.Event import EventWithTiersRead , EventUpdateWithTiers
from services.Organizer_services import update_event_with_tiers
@app.put("/update_event/{id}", response_model=EventWithTiersRead)
def update_event(
    id: int,
    event_data: EventUpdateWithTiers,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return update_event_with_tiers(id, event_data, user, session)


# Customer Session: 
from datetime import datetime
@app.get("/events/customer", response_model=List[EventRead])
def search_events(
    session: Session = Depends(get_session),
    search: Optional[str] = Query(None),
    venue: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
):
    return search_events_customer(
        session, search, venue, city, country, category,
        date_from, date_to, min_price, max_price
    )

# placing the order :
from services.Order_services import book_ticket
@app.post("/orders" ,  response_model=OrderRead)
def create_order(
    order_data: OrderCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return book_ticket(order_data, user, session)


@app.get("/orders/me", response_model=List[OrderRead])
def my_orders(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_my_orders(user, session)

@app.post("/orders/{order_id}/checkout")
def checkout_order(
    order_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return create_checkout_session(order_id, user, session)


# webhook for payment:
from fastapi import Request
from services.Payment_services import handle_stripe_webhook

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.body()
    logging.info(f"Received webhook payload, length: {len(payload)}")
    sig_header = request.headers.get("stripe-signature")
    return handle_stripe_webhook(payload, sig_header, session)

@app.get("/events/customer/{id}", response_model=EventWithTiersRead)
def public_event_detail(id: int, session: Session = Depends(get_session)):
    return get_public_event_detail(id, session)


# Getting order status and sending to the afterward stripe page:
from services.Order_services import get_order_status
@app.get("/orders/{order_id}", response_model=OrderRead)
def order_status(
    order_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_order_status(order_id, user, session)


@app.get("/organizer/fraud-orders")
def fraud_orders(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_fraud_orders(user, session)

from services.qr_service import get_ticket_qr , check_in_ticket


@app.get("/tickets/{ticket_uid}/qr")
def Get_Ticket_qr(ticket_uid: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_ticket_qr(ticket_uid , user , session)

@app.post("/checkin/{ticket_uid}")
def checkin(ticket_uid: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return check_in_ticket(ticket_uid, session)