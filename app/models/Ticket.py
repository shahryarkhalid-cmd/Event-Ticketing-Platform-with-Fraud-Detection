from sqlmodel import SQLModel, Field
from typing import Optional

class TicketTier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    category_name: str          
    price: float
    currency: str               
    total_seats: int          
    sold_quantity: int = Field(default=0)
    benefits_included: Optional[str] = None
    description: Optional[str] = None
    
    
    
from pydantic import BaseModel
from typing import List

class TicketTierCreate(BaseModel):
    category_name: str
    price: float
    currency: str  
    total_seats: int
    benefits_included: Optional[str] = None
    description: Optional[str] = None
    
    
class TicketTierRead(BaseModel):
    id: int
    category_name: str
    price: float
    currency: str
    total_seats: int
    sold_quantity: int
    benefits_included: Optional[str] = None
    description: Optional[str] = None

class TicketTierBulkCreate(BaseModel):
    tiers: List[TicketTierCreate]