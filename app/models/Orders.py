from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel , Field


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    ticket_tier_id: int = Field(foreign_key="tickettier.id")
    quantity: int
    total_price: float
    status: str = Field(default="pending")  # pending, paid, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    

class OrderCreate(BaseModel):
    ticket_tier_id: int
    quantity: int

class OrderRead(BaseModel):
    id: int
    user_id: int
    ticket_tier_id: int
    quantity: int
    total_price: float
    status: str
    created_at: datetime