from models.Event import Event
from typing import Optional
from sqlmodel import Session , select
def search_events_customer(
    session: Session,
    search: Optional[str],
    venue: Optional[str],
    city: Optional[str],
    country: Optional[str],
    category: Optional[str],
):
    query = select(Event)
    if search:
        query = query.where(Event.name.ilike(f"%{search}%"))
    if venue:
        query = query.where(Event.venue.ilike(f"%{venue}%"))
    if city:
        query = query.where(Event.city.ilike(f"%{city}%"))
    if country:
        query = query.where(Event.country.ilike(f"%{country}%"))
    if category:
        query = query.where(Event.category == category)

    events = session.exec(query).all()
    return events