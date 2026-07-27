
from sqlmodel import Session , select
from models.Orders import OrderCreate , Order , CartItem ,OrderItem , OrderRead
from models.Ticket import TicketTier
from models.Users import User , UserRole
import logging
from dependencies.exception import Not_customer , Ticket_Tier_not_found , Order_Quantity_Error , Not_Enough_Tickets , BookingContention
from core.redis_client import redis_client
from core.locking import acquire_lock , release_lock
def book_cart(order_data: OrderCreate, user: User, session: Session):
    if user.role != UserRole.customer:
        raise Not_customer()
    if not order_data.items:
        raise Not_customer()

    sorted_items = sorted(order_data.items, key=lambda i: i.ticket_tier_id)
    acquired_locks = []

    try:
        for item in sorted_items:
            if item.quantity <= 0:
                raise Order_Quantity_Error()
            resource_key = f"tier:{item.ticket_tier_id}"
            lock_id = acquire_lock(redis_client, resource_key)
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
            session.add(tier)

            subtotal = tier.price * item.quantity
            total_price += subtotal
            order_items.append((tier, item.quantity, subtotal))

        new_order = Order(
            user_id=user.id,
            event_id=order_data.event_id,
            total_price=total_price,
            status="pending"
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

        session.commit()
        session.refresh(new_order)
        return new_order

    finally:
        for resource_key, lock_id in acquired_locks:
            release_lock(redis_client, resource_key, lock_id)


def get_my_orders(user: User, session: Session):
    orders = session.exec(select(Order).where(Order.user_id == user.id)).all()
    return orders