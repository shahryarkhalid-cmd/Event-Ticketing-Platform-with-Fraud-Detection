# app/services/Payment_services.py
import stripe
from fastapi import HTTPException
from sqlmodel import Session
from models.Orders import Order
from models.Users import User
from dependencies.exception import Not_Order , Order_Mismatch , Not_Pending_Order
import os
from dotenv import load_dotenv
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(order_id: int, user: User, session: Session):
    order = session.get(Order, order_id)
    if not order:
        raise Not_Order()
    if order.user_id != user.id:
        raise Order_Mismatch()
    if order.status != "pending":
        raise Not_Pending_Order()

    amount_in_smallest_unit = int(order.total_price * 100)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",  # hardcoded for now — we'll handle multi-currency next
                "product_data": {
                    "name": f"Order #{order.id}",
                },
                "unit_amount": amount_in_smallest_unit,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="http://localhost:3000/payment-success?order_id=" + str(order.id),
        cancel_url="http://localhost:3000/payment-cancelled?order_id=" + str(order.id),
        metadata={"order_id": str(order.id)}  # important — explained below
    )

    return {"checkout_url": checkout_session.url}