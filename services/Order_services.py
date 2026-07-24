
from sqlmodel import Session , select
from models.Orders import OrderCreate , Order
from models.Ticket import TicketTier
from models.Users import User , UserRole
import logging
from dependencies.exception import Not_customer , Ticket_Tier_not_found , Order_Quantity_Error , Not_Enough_Tickets , BookingContention
from core.redis_client import redis_client
from core.locking import acquire_lock , release_lock
def book_ticket(order_data: OrderCreate, user: User, session: Session):
    if user.role != UserRole.customer:
        logging.warning(f"User {user.id} with role {user.role} attempted to book a ticket")
        raise Not_customer()

    if order_data.quantity <= 0:
        raise Order_Quantity_Error()

    resource_key = f"tier:{order_data.ticket_tier_id}"
    lock_id = acquire_lock(redis_client, resource_key)
    print(f"LOCK ATTEMPT for {resource_key}: {'ACQUIRED' if lock_id else 'FAILED'}")

    if lock_id is None:
        logging.warning(f"Could not acquire lock for {resource_key} — high contention")
        raise BookingContention()

    try:
        tier = session.get(TicketTier, order_data.ticket_tier_id)
        if not tier:
            raise Ticket_Tier_not_found()

        available = tier.total_seats - tier.sold_quantity
        if order_data.quantity > available:
            raise Not_Enough_Tickets()

        tier.sold_quantity += order_data.quantity
        session.add(tier)
        new_order = Order(
            user_id=user.id,
            event_id=tier.event_id,
            ticket_tier_id=tier.id,
            quantity=order_data.quantity,
            total_price=tier.price * order_data.quantity,
            status="pending"
        )
        session.add(new_order)
        session.flush()
        session.refresh(new_order)
        logging.info(f"Order {new_order.id} created for user {user.id}, tier {tier.id}")
        return new_order

    finally:
        release_lock(redis_client, resource_key, lock_id)


def get_my_orders(user: User, session: Session):
    if user.role != UserRole.customer:
            raise Not_customer()
    orders = session.exec(select(Order).where(Order.user_id == user.id)).all()
    return orders