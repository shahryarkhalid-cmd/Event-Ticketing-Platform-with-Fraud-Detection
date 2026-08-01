# app/services/qr_service.py
import qrcode
import io
from fastapi.responses import StreamingResponse

def generate_qr_image_response(data: str) -> StreamingResponse:
    qr = qrcode.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")

from dependencies.exception import Ticket_Not_Found , Not_Your_Ticket , Invalid_Ticket , Ticket_Already_Used , Ticket_Cancelled , Forbidden
from models.Users import User
from sqlmodel import Session , select
from models.Ticket_entity import Ticket as TicketInstance
from models.Orders import OrderItem , Order


def get_ticket_qr(ticket_uid: str, user: User, session: Session):
    ticket = session.exec(select(TicketInstance).where(TicketInstance.ticket_uid == ticket_uid)).first()
    if not ticket:
        raise Ticket_Not_Found()
    
    # Ownership check: verify this ticket belongs to the requesting user
    order_item = session.get(OrderItem, ticket.order_item_id)
    order = session.get(Order, order_item.order_id)
    if order.user_id != user.id:
        raise Not_Your_Ticket()
    
    return generate_qr_image_response(ticket.ticket_uid)

from models.Users import UserRole
from datetime import datetime , timezone
def check_in_ticket(ticket_uid: str, user , session: Session):
    
    if user.role != UserRole.organizer:
        raise Forbidden()
    
    ticket = session.exec(select(TicketInstance).where(TicketInstance.ticket_uid == ticket_uid)).first()
    if not ticket:
        raise Invalid_Ticket()
    if ticket.status == "used":
        raise Ticket_Already_Used()
    if ticket.status == "cancelled":
        raise Ticket_Cancelled()

    ticket.status = "used"
    ticket.checked_in_at = datetime.now(timezone.utc)
    session.add(ticket)
    session.flush()
    return {"message": "Checked in successfully", "ticket_uid": ticket.ticket_uid}