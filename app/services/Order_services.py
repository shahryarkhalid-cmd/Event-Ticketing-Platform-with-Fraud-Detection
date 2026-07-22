
from sqlmodel import Session , select
from models.Orders import OrderCreate , Order
from models.Ticket import TicketTier
from models.Users import User , UserRole
from dependencies.exception import Not_customer , Ticket_Tier_not_found , Order_Quantity_Error , Not_Enough_Tickets
def book_ticket(order_data: OrderCreate, user: User, session: Session):
    tier = session.get(TicketTier, order_data.ticket_tier_id)
    if user.role != UserRole.customer:
        raise Not_customer()
    if not tier:
        raise Ticket_Tier_not_found()

    available = tier.total_seats - tier.sold_quantity
    if order_data.quantity <= 0:
        raise Order_Quantity_Error()
    if order_data.quantity > available:
        raise Not_Enough_Tickets()

    tier.sold_quantity += order_data.quantity
    session.add(tier)

    new_order = Order(
        user_id=user.id,
        ticket_tier_id=tier.id,
        quantity=order_data.quantity,
        total_price=tier.price * order_data.quantity,
        status="pending"
    )
    session.add(new_order)
    session.flush()
    session.refresh(new_order)
    return new_order


def get_my_orders(user: User, session: Session):
    if user.role != UserRole.customer:
            raise Not_customer()
    orders = session.exec(select(Order).where(Order.user_id == user.id)).all()
    return orders