# app/services/Payment_services.py
import stripe
from sqlmodel import Session , select
from models.Orders import Order , OrderItem
from models.Ticket import TicketTier
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

    order_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()

    line_items = []
    for item in order_items:
        tier = session.get(TicketTier, item.ticket_tier_id)
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"{tier.category_name} Ticket"},
                "unit_amount": int(tier.price * 100),
            },
            "quantity": item.quantity,
        })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url="http://localhost:3000/payment-success?order_id=" + str(order.id),
        cancel_url="http://localhost:3000/payment-cancelled?order_id=" + str(order.id),
        metadata={"order_id": str(order.id)}
    )

    return {"checkout_url": checkout_session.url}


# app/services/Payment_services.py
import os
import stripe
import logging
from sqlmodel import Session
from models.Orders import Order
from dependencies.exception import InvalidWebhookPayload, InvalidWebhookSignature

def handle_stripe_webhook(payload: bytes, sig_header: str, session: Session):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        logging.error("Stripe webhook: invalid payload received")
        raise InvalidWebhookPayload()
    except stripe.error.SignatureVerificationError:
        logging.error("Stripe webhook: signature verification failed")
        raise InvalidWebhookSignature()

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        order_id = int(session_data["metadata"]["order_id"])

        order = session.get(Order, order_id)
        if order and order.status == "pending":
            order.status = "paid"
            session.add(order)
            session.commit()
            logging.info(f"Order {order_id} marked as paid via Stripe webhook")
        elif not order:
            logging.warning(f"Stripe webhook: order {order_id} not found")
        else:
            logging.info(f"Stripe webhook: order {order_id} already in status '{order.status}', ignoring")

    return {"status": "success"}