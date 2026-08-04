from models.Event import Event
from typing import Optional
from sqlmodel import Session , select
from sqlalchemy import func
from models.Ticket import TicketTier
from datetime import datetime
def search_events_customer(
    session: Session,
    search: Optional[str],
    venue: Optional[str],
    city: Optional[str],
    country: Optional[str],
    category: Optional[str],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
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
    if date_from:
        query = query.where(Event.start_datetime >= date_from)
    if date_to:
        query = query.where(Event.start_datetime <= date_to)

    events = session.exec(query).all()

    # Price filtering requires checking each event's tiers, since price lives on TicketTier
    if min_price is not None or max_price is not None:
        filtered = []
        for event in events:
            tiers = session.exec(select(TicketTier).where(TicketTier.event_id == event.id)).all()
            if not tiers:
                continue
            prices = [t.price for t in tiers]
            lowest = min(prices)
            if min_price is not None and lowest < min_price:
                continue
            if max_price is not None and lowest > max_price:
                continue
            filtered.append(event)
        events = filtered

    return events

from dependencies.exception import Event_Not_Found
def get_public_event_detail(id: int, session: Session):
    event = session.get(Event, id)
    if not event:
        raise Event_Not_Found()
    
    tiers = session.exec(select(TicketTier).where(TicketTier.event_id == id)).all()
    return {"event": event, "ticket_tiers": tiers}



from sqlmodel import Session, select, func
from models.Event import Event

def get_event_categories_with_counts(session: Session):
    results = session.exec(
        select(Event.category, func.count(Event.id))
        .group_by(Event.category)
    ).all()

    return [
        {"category": category, "count": count}
        for category, count in results
    ]