from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List 
class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")  # whose mailbox this belongs to
    title: str                                    # "Payment successful"
    body: str                                     # "Your payment of $190 was confirmed."
    is_read: bool = Field(default=False)          # has the user seen it yet?
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))