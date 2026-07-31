from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel , Field


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    ticket_tier_id: int = Field(foreign_key="tickettier.id")
    quantity: int
    subtotal: float

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    total_price: float
    payment_status: str = Field(default="pending")  # pending, paid, refunded
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fraud_status: Optional[str] = None  # null, fraud_review, under_review, confirmed_fraud, dismissed
    fraud_reason: Optional[str] = None
    fraud_score: Optional[float] = None

from typing import List

class CartItem(BaseModel):
    ticket_tier_id: int
    quantity: int

class OrderCreate(BaseModel):
    event_id: int
    items: List[CartItem]
    

class OrderItemRead(BaseModel):
    id: int
    ticket_tier_id: int
    quantity: int
    subtotal: float

class OrderRead(BaseModel):
    id: int
    user_id: int
    event_id: int
    total_price: float
    payment_status: str
    fraud_status: Optional[str] = None
    created_at: datetime