# app/models/event.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    venue: str
    date: datetime
    organizer_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    
class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    venue: str
    date: datetime

class EventRead(BaseModel):
    id : int = Field(default = None)
    name: str
    description: Optional[str] = None
    venue: str
    date: datetime