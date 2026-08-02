from fastapi import FastAPI , Depends , Request
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
            , not_your_ticket , ticket_not_found , invalid_ticket , Invalid_Ticket , ticket_already_used , Ticket_Already_Used)
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

# Adding Rate Limiting:
# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
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

app.state.limiter = limiter
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
app.add_exception_handler(Invalid_Ticket , invalid_ticket)
app.add_exception_handler(Ticket_Already_Used , ticket_already_used)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("5/minute")
def login(request : Request ,user : UserLogin , session : Session = Depends(get_session)):
    return logging_in(user , session)

# Returns the logged-in user's profile, including whether they have
# already picked a role. The frontend calls this right after login/signup
# to decide: role-selection page (first time) vs. straight to dashboard.
@app.get('/users/me', response_model=UserRead)
def read_current_user(user: User = Depends(get_current_user) ,session : Session = Depends(get_session)):
    return get_me(user , session)

# One-time role selection (customer or organizer). Locked after first use.
@app.post('/auth/select-role')
def choose_role(
    role_data: RoleSelect,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return select_role(role_data, user, session)

@app.post("/publish-event")
@limiter.limit("5/month")
def publish_event_route(
    request : Request ,
    event_data: EventCreateWithTiers,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return Make_Event(event_data, user, session)


@ app.get('/get_all_events')
@limiter.limit("5/minute")
def get_all_event( request : Request ,user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
    return get_organizer_events(user , session)

@ app.get('/get_event/{id}')
@limiter.limit("5/minute")
def get_event(request : Request , id : int , user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
    return get_specific_event(id , user , session)

@ app.delete('/delete_event/{id}')
@limiter.limit("5/minute")
def delete_event( request : Request ,id : int , user : User = Depends(get_current_user), session : Session = Depends(get_session)):
    return delete_organizer_event(id , user , session)

@ app.delete('/delete_all_event')
@limiter.limit("5/minute")
def delete_all_event(request : Request ,user : User = Depends(get_current_user) , session : Session = Depends(get_session)):
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
    return check_in_ticket(ticket_uid, user ,  session)


# For Fraud Detection Dashboard:
from services.Organizer_services import update_fraud_status
@app.post("/organizer/fraud-orders/{order_id}/review")
def mark_under_review(order_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return update_fraud_status(order_id, "under_review", user, session)

@app.post("/organizer/fraud-orders/{order_id}/confirm")
def confirm_fraud(order_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return update_fraud_status(order_id, "confirmed_fraud", user, session)

@app.post("/organizer/fraud-orders/{order_id}/dismiss")
def dismiss_fraud(order_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return update_fraud_status(order_id, "dismissed", user, session)

from services.Order_services import get_order_tickets
# Getting order Tickets :
@app.get("/orders/{order_id}/tickets")
def order_tickets(
    order_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_order_tickets(order_id, user, session)

from fastapi import  UploadFile, File, Depends
from services.Banner_services import upload_event_banner_service
# Adding Banner Services:
# routes/event_routes.py
@app.post("/events/{event_id}/banner")
async def upload_event_banner(
    event_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return await upload_event_banner_service(event_id, file, current_user, session)


# Addin pic of the User:
from services.User_services import upload_profile_picture_service
# routes/user_routes.py
@app.post("/users/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return await upload_profile_picture_service(file, current_user, session)



# Updating the user information :

# routes/user_routes.py
from models.Users import UserUpdate
from services.User_services import update_user_profile_service
@app.patch("/users/me/update", response_model=UserRead)
def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return update_user_profile_service(update_data, current_user, session)

# Updating the password:
from models.Users import PasswordChange
from services.User_services import change_password
@app.post("/users/me/change-password")
def update_password(
    password_data: PasswordChange,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return change_password(password_data, user, session)
from services.Order_services import get_my_booking_history
# Getting the booking History:
@app.get("/users/me/booking-history")
def booking_history(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_my_booking_history(user, session)


# Notification session:

from services.Notification_services import get_notifications , mark_notification_read , delete_notification
@app.get("/notifications")
def notifications(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_notifications(user, session)

@app.post("/notifications/{notification_id}/read")
def read_notification(notification_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return mark_notification_read(notification_id, user, session)

@app.delete("/notifications/delete")
def delete_notifications(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return delete_notification(user, session)



# AUTH OTP : 
from fastapi import HTTPException
from services.Verification_service import verify_otp , generate_and_send_otp
from models.Users import OTPVerify, ResendVerification

@app.post("/auth/verify-email")
def verify_email(otp_data: OTPVerify, session: Session = Depends(get_session)):
    return verify_otp(otp_data.email, otp_data.code, session)


@app.post("/auth/resend-verification")
def resend_verification(data: ResendVerification, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(404, "No account found with this email")
    if user.is_verified:
        raise HTTPException(400, "This account is already verified")

    return generate_and_send_otp(user.email)


# FORGOT PASSWORD:
from services.Password_reset_service import request_password_reset, verify_reset_code, reset_password
from models.Users import ForgotPasswordRequest, VerifyResetCode, ResetPasswordConfirm

@app.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordRequest, session: Session = Depends(get_session)):
    return request_password_reset(data.email, session)

@app.post("/auth/verify-reset-code")
def verify_reset_code_route(data: VerifyResetCode, session: Session = Depends(get_session)):
    return verify_reset_code(data.email, data.code, session)

@app.post("/auth/reset-password")
def reset_password_route(data: ResetPasswordConfirm, session: Session = Depends(get_session)):
    return reset_password(data.reset_token, data.new_password, session)