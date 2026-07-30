# app/models/ticket.py (new file — don't confuse with your existing TicketTier)
import uuid
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_item_id: int = Field(foreign_key="orderitem.id")
    ticket_uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    status: str = Field(default="valid")  # valid, used, cancelled
    checked_in_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))