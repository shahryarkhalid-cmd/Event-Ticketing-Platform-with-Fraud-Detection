from fastapi import Depends
from sqlmodel import Session , select
from models.Event import EventCreateWithTiers , Event
from models.Users import User
import logging
from dependencies.exception import Forbidden ,Event_Not_Found
from models.Ticket import TicketTierBulkCreate , TicketTier
def Make_Event( event_data : EventCreateWithTiers , user : User , session : Session):
    user_info = session.exec(select(User).where(User.email == user.email)).first()
    if user_info.role != "organizer":
        logging.error("User is not Organizer!")
        raise Forbidden()
    new_event = Event(
        name=event_data.name,
        category=event_data.category,
        description=event_data.description,
        venue=event_data.venue,
        address=event_data.address,
        city=event_data.city,
        country=event_data.country,
        start_datetime=event_data.start_datetime,
        end_datetime=event_data.end_datetime,
        max_capacity=event_data.max_capacity,
        dress_code=event_data.dress_code,
        age_restriction=event_data.age_restriction,
        parking_available=event_data.parking_available,
        food_available=event_data.food_available,
        refund_policy=event_data.refund_policy,
        terms_accepted=event_data.terms_accepted,
        organizer_id=user.id
    )
    session.add(new_event)
    session.flush()
    session.refresh(new_event)
    created_tiers = []
    for tier in event_data.ticket_tiers:
        new_tier = TicketTier(
            event_id=new_event.id,
            category_name=tier.category_name,
            price=tier.price,
            currency=tier.currency,
            total_seats=tier.total_seats,
            benefits_included=tier.benefits_included,
            description=tier.description
        )
        session.add(new_tier)
        created_tiers.append(new_tier)
    session.commit()
    session.refresh(new_event)
    for tier in created_tiers:
        session.refresh(tier)

    return {"event": new_event, "ticket_tiers": created_tiers}


def get_organizer_events(user : User , session : Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
 
    listed_events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    logging.info("Listing the events")
    return listed_events
    
    
def delete_organizer_event(id : int , user : User , session : Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    to_delete = session.exec(select(Event).where(Event.id == id)).first()
    session.delete(to_delete)
    return {"message" : "Deleted sucessfully"}


def delete_all_organizer_event(user , session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    to_delete = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    for d in to_delete:
        session.delete(d)
    logging.info("Deleted all organizer events")
    return {'message' : 'Deleted sucessfully'}

def get_specific_event(id , user , session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    to_find = session.exec(select(Event).where(Event.id == id , Event.organizer_id == user.id)).first()
    if not to_find:
        raise Event_Not_Found()
    logging.info('Specific event returned sucessfully')
    return to_find



# Creating the Ticket:
def add_ticket_tiers(event_id: int, tiers_data: TicketTierBulkCreate, user: User, session: Session):
    event = session.get(Event, event_id)
    if not event:
        logging.error("Event not found")
        raise Event_Not_Found()
    if event.organizer_id != user.id:
        logging.error("User not organizer")
        raise Forbidden()

    created_tiers = []
    for tier in tiers_data.tiers:
        new_tier = TicketTier(
            event_id=event_id,
            tier_name=tier.tier_name,
            price=tier.price,
            total_quantity=tier.total_quantity
        )
        session.add(new_tier)
        created_tiers.append(new_tier)

    session.flush()
    for tier in created_tiers:
        session.refresh(tier)

    return created_tiers
    
def List_Tickets(event_id : int , user : User , session : Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    event = session.get(Event, event_id)
    if not event:
        logging.error("Event not found")
        raise Event_Not_Found()
     
    tiers = session.exec(select(TicketTier).where(TicketTier.event_id == event_id)).all()
    return tiers


def get_analytics_summary(user: User, session: Session):
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    total_events = len(events)
    upcoming_events = len([e for e in events if e.start_datetime > datetime.now(timezone.utc)])

    paid_orders = session.exec(
        select(Order).where(Order.event_id.in_(event_ids), Order.status == "paid")
    ).all() if event_ids else []

    tickets_sold = sum(o.quantity for o in paid_orders)
    total_revenue = sum(o.total_price for o in paid_orders)

    return {
        "tickets_sold": tickets_sold,
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "total_revenue": total_revenue
    }