from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List 
from app.models.Ticket import TicketTierCreate, TicketTierRead
class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Basic info
    name: str
    category: str 
    description: Optional[str] = None
    
    # Venue and location
    venue: str
    address: str
    city: str
    country: str
    
    # Date and time
    start_datetime: datetime
    end_datetime: datetime
    
    max_capacity: int
    dress_code: Optional[str] = None
    age_restriction: Optional[int] = None 
    parking_available: bool = Field(default=False)
    food_available: bool = Field(default=False)
    refund_policy: Optional[str] = None
    terms_accepted: bool = Field(default=False)
    
    organizer_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    
class EventCreateWithTiers(BaseModel):
    # Basic info
    name: str
    category: str
    description: Optional[str] = None
    # Venue
    venue: str
    address: str
    city: str
    country: str
    # Date/time
    start_datetime: datetime
    end_datetime: datetime
    # Capacity/policies
    max_capacity: int
    dress_code: Optional[str] = None
    age_restriction: Optional[int] = None
    parking_available: bool = False
    food_available: bool = False
    refund_policy: Optional[str] = None
    terms_accepted: bool

    ticket_tiers: List[TicketTierCreate]

class EventRead(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    venue: str
    address: str
    city: str
    country: str

    start_datetime: datetime
    end_datetime: datetime

    max_capacity: int
    dress_code: Optional[str] = None
    age_restriction: Optional[int] = None
    parking_available: bool
    food_available: bool
    refund_policy: Optional[str] = None
    terms_accepted: bool

    organizer_id: int
    created_at: datetime
    
    

class EventWithTiersRead(BaseModel):
    event: EventRead
    ticket_tiers: List[TicketTierRead]
    
    
class EventUpdateWithTiers(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    venue: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    max_capacity: Optional[int] = None
    dress_code: Optional[str] = None
    age_restriction: Optional[int] = None
    parking_available: Optional[bool] = None
    food_available: Optional[bool] = None
    refund_policy: Optional[str] = None
    ticket_tiers: Optional[List[TicketTierCreate]] = None
    
class EventWithTiersRead(BaseModel):
    event: EventRead
    ticket_tiers: List[TicketTierRead]