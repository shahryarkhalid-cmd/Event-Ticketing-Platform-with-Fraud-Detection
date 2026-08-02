
from sqlmodel import Session , select
from models.Orders import OrderCreate , Order , CartItem ,OrderItem , OrderRead
from models.Ticket import TicketTier
from models.Users import User , UserRole
import logging
from dependencies.exception import Not_customer , Ticket_Tier_not_found , Order_Quantity_Error , Not_Enough_Tickets , BookingContention
from core.redis_client import redis_client
from core.locking import acquire_lock , release_lock
from services.fraud_detection import predict_order, fraud_config
from models.Notification import Notification
def book_ticket(order_data: OrderCreate, user: User, session: Session):
    if user.role != UserRole.customer:
        raise Not_customer()
    if not order_data.items:
        raise Order_Quantity_Error()

    sorted_items = sorted(order_data.items, key=lambda i: i.ticket_tier_id)
    acquired_locks = []

    try:
        for item in sorted_items:
            resource_key = f"tier:{item.ticket_tier_id}"
            lock_id = acquire_lock(redis_client, resource_key)
            logging.info(f"LOCK ATTEMPT for {resource_key}: {'ACQUIRED' if lock_id else 'FAILED'}")
            if lock_id is None:
                raise BookingContention()
            acquired_locks.append((resource_key, lock_id))

        order_items = []
        total_price = 0.0

        for item in sorted_items:
            tier = session.get(TicketTier, item.ticket_tier_id)
            if not tier:
                raise Ticket_Tier_not_found()
            available = tier.total_seats - tier.sold_quantity
            if item.quantity > available:
                raise Not_Enough_Tickets()

            tier.sold_quantity += item.quantity
            if tier.sold_quantity >= tier.total_seats:
                    event = session.get(Event, tier.event_id)
                    session.add(Notification(
                        user_id=event.organizer_id,
                        type="sold_out",
                        title="Tickets sold out",
                        body=f"{tier.category_name} for '{event.name}' is now fully booked."
                    ))
            session.add(tier)

            subtotal = tier.price * item.quantity
            total_price += subtotal
            order_items.append((tier, item.quantity, subtotal))

        new_order = Order(
            user_id=user.id,
            event_id=order_data.event_id,
            total_price=total_price,
            payment_status="pending"
        )
        session.add(new_order)
        session.flush()

        for tier, qty, subtotal in order_items:
            session.add(OrderItem(
                order_id=new_order.id,
                ticket_tier_id=tier.id,
                quantity=qty,
                subtotal=subtotal
            ))

        fraud_prediction = predict_order(new_order, user, order_items, session)
        logging.info(
            "Fraud prediction: is_fraud=%s probability=%.4f reason=%s",
            fraud_prediction.is_fraud,
            fraud_prediction.fraud_probability,
            fraud_prediction.reason,
        )
        if fraud_prediction.is_fraud:
            new_order.fraud_status = "fraud_review"
            new_order.fraud_reason = fraud_prediction.reason
            new_order.fraud_score = fraud_prediction.fraud_probability
# payment_status stays "pending" by default — fraud flag no longer blocks payment status

        session.flush()
        session.refresh(new_order)
        return new_order

    finally:
        for resource_key, lock_id in acquired_locks:
            release_lock(redis_client, resource_key, lock_id)

def get_my_orders(user: User, session: Session):
    orders = session.exec(select(Order).where(Order.user_id == user.id)).all()
    return orders

from fastapi import HTTPException
# get_order_status:

from models.Ticket_entity import Ticket as TicketInstance
def get_order_status(order_id: int, user: User, session: Session):
    order = session.get(Order, order_id)
    if not order:
         raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    return order


def get_order_tickets(order_id: int, user: User, session: Session):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your order")

    items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    item_ids = [i.id for i in items]

    tickets = session.exec(
        select(TicketInstance).where(TicketInstance.order_item_id.in_(item_ids))
    ).all() if item_ids else []

    result = []
    for ticket in tickets:
        item = session.get(OrderItem, ticket.order_item_id)
        tier = session.get(TicketTier, item.ticket_tier_id) if item else None
        result.append({
            "ticket_uid": ticket.ticket_uid,
            "status": ticket.status,
            "category_name": tier.category_name if tier else "Unknown",
        })
    return result

# Getting my Booking History:
from models.Event import Event

def get_my_booking_history(user: User, session: Session):
    orders = session.exec(select(Order).where(Order.user_id == user.id)).all()
    result = []
    for order in orders:
        event = session.get(Event, order.event_id)
        result.append({
            "order_id": order.id,
            "event_name": event.name if event else "Unknown",
            "total_price": order.total_price,
            "status": order.payment_status
        })
    return result