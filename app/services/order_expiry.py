# app/services/order_expiry.py
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from models.Orders import Order, OrderItem
from models.Ticket import TicketTier
import logging

def expire_stale_orders(session: Session):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=20)
    stale_orders = session.exec(
        select(Order).where(
            Order.payment_status == "pending",
            Order.created_at < cutoff
        )
    ).all()

    for order in stale_orders:
        items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in items:
            tier = session.get(TicketTier, item.ticket_tier_id)
            if tier:
                tier.sold_quantity = max(0, tier.sold_quantity - item.quantity)
                session.add(tier)
        order.payment_status = "expired"
        session.add(order)
        logging.info(f"Order {order.id} expired — seats released")

    if stale_orders:
        session.commit()

    return len(stale_orders)