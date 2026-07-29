from fastapi import Depends
from sqlmodel import Session , select
from models.Event import EventCreateWithTiers , Event
from models.Users import User
import logging
from dependencies.exception import Forbidden ,Event_Not_Found
from models.Ticket import TicketTier
from models.Orders import OrderItem
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
    if not to_delete:
       raise Event_Not_Found()
    tiers = session.exec(select(TicketTier).where(TicketTier.event_id == id)).all()
    logging.info(f"FOUND {len(tiers)} TIERS TO DELETE FOR EVENT {id}")
    for tier in tiers:
        session.delete(tier)
    session.flush()
    session.delete(to_delete)
    session.flush()
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




def List_Tickets(event_id : int , user : User , session : Session):
    # Ticket tiers (prices, remaining seats, etc.) are needed by customers
    # to browse and book — this is not an organizer-only action, so any
    # authenticated user (customer or organizer) may view them.
    event = session.get(Event, event_id)
    if not event:
        logging.error("Event not found")
        raise Event_Not_Found()
     
    tiers = session.exec(select(TicketTier).where(TicketTier.event_id == event_id)).all()
    return tiers


# Dashboard analytic summary :
def get_analytics_summary(user: User, session: Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    total_events = len(events)
    upcoming_events = len([
        e for e in events
        if e.start_datetime > datetime.now(timezone.utc).replace(tzinfo=None)
    ])

    paid_orders = session.exec(
        select(Order).where(Order.event_id.in_(event_ids), Order.status == "paid")
    ).all() if event_ids else []

    order_ids = [o.id for o in paid_orders]
    items = session.exec(select(OrderItem).where(OrderItem.order_id.in_(order_ids))).all() if order_ids else []
    tickets_sold = sum(i.quantity for i in items)
    total_revenue = sum(o.total_price for o in paid_orders)

    return {
        "tickets_sold": tickets_sold,
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "total_revenue": total_revenue
    }
    


from datetime import timedelta , timezone , datetime
from models.Orders import Order

def get_ticket_sales_last_7_days(user: User, session: Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    orders = session.exec(
        select(Order).where(
            Order.event_id.in_(event_ids),
            Order.status == "paid",
            Order.created_at >= seven_days_ago
        )
    ).all() if event_ids else []

    order_ids = [o.id for o in orders]
    items = session.exec(select(OrderItem).where(OrderItem.order_id.in_(order_ids))).all() if order_ids else []
    item_to_order = {o.id: o for o in orders}

    daily_counts = {}
    for item in items:
        order = item_to_order[item.order_id]
        day = order.created_at.strftime("%a")
        daily_counts[day] = daily_counts.get(day, 0) + item.quantity

    return daily_counts


def get_popular_ticket_categories(user: User, session: Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    orders = session.exec(
        select(Order).where(Order.event_id.in_(event_ids), Order.status == "paid")
    ).all() if event_ids else []
    order_ids = [o.id for o in orders]
    items = session.exec(select(OrderItem).where(OrderItem.order_id.in_(order_ids))).all() if order_ids else []

    category_counts = {}
    for item in items:
        tier = session.get(TicketTier, item.ticket_tier_id)
        category_counts[tier.category_name] = category_counts.get(tier.category_name, 0) + item.quantity

    return category_counts


def get_organizer_all_bookings(user: User, session: Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    orders = session.exec(select(Order).where(Order.event_id.in_(event_ids))).all() if event_ids else []
    order_ids = [o.id for o in orders]
    items = session.exec(select(OrderItem).where(OrderItem.order_id.in_(order_ids))).all() if order_ids else []
    order_map = {o.id: o for o in orders}

    result = []
    for item in items:
        order = order_map[item.order_id]
        customer = session.get(User, order.user_id)
        tier = session.get(TicketTier, item.ticket_tier_id)
        event = session.get(Event, order.event_id)
        result.append({
            "customer": customer.full_name,
            "email": customer.email,
            "event": event.name,
            "category": tier.category_name,
            "qty": item.quantity,
            "amount": item.subtotal,
            "date": order.created_at,
            "status": order.status,
            "qr_generated": False  # Order no longer has qr_code — deferred feature per your earlier decision
        })
    return result


def get_revenue_overview(user: User, session: Session):
    if user.role != "organizer":
            logging.error("User is not the organizer")
            raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    all_orders = session.exec(select(Order).where(Order.event_id.in_(event_ids))).all() if event_ids else []

    paid_orders = [o for o in all_orders if o.status == "paid"]
    refunded_orders = [o for o in all_orders if o.status == "refunded"]

    total_revenue = sum(o.total_price for o in paid_orders)
    refunded_amount = sum(o.total_price for o in refunded_orders)
    avg_order_value = total_revenue / len(paid_orders) if paid_orders else 0
    net_revenue = total_revenue - refunded_amount

    return {
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "refunded": refunded_amount,
        "net_revenue": net_revenue
    }

def get_monthly_revenue_trend(user: User, session: Session):
    if user.role != "organizer":
            logging.error("User is not the organizer")
            raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    paid_orders = session.exec(
        select(Order).where(Order.event_id.in_(event_ids), Order.status == "paid")
    ).all() if event_ids else []

    monthly = {}
    for order in paid_orders:
        month = order.created_at.strftime("%b")  # "Feb", "Mar"...
        monthly[month] = monthly.get(month, 0) + order.total_price

    return monthly

from dependencies.exception import Paid_Refund , Not_Your_Event
def refund_order(order_id: int, user: User, session: Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    event = session.get(Event, order.event_id)
    if event.organizer_id != user.id:
        raise Not_Your_Event()
    if order.status != "paid":
        raise Paid_Refund()

    order.status = "refunded"

    # Give back seats for every tier in this order, not just one
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    for item in items:
        tier = session.get(TicketTier, item.ticket_tier_id)
        tier.sold_quantity -= item.quantity
        session.add(tier)

    session.add(order)
    session.flush()  # matches your centralized-commit pattern from earlier
    return order

from models.Event import EventUpdateWithTiers
from sqlalchemy import func
from fastapi import HTTPException
def update_event_with_tiers(id: int, event_data: EventUpdateWithTiers, user: User, session: Session):
    if user.role != "organizer":
        raise Forbidden()

    event = session.exec(select(Event).where(Event.id == id)).first()
    if not event:
        raise Event_Not_Found()
    if event.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="Not your event")

    update_dict = event_data.dict(exclude_unset=True, exclude={"ticket_tiers"})
    for field, value in update_dict.items():
        setattr(event, field, value)
    session.add(event)

    new_tiers = []
    if event_data.ticket_tiers is not None:
        existing_tiers = session.exec(select(TicketTier).where(TicketTier.event_id == id)).all()

        locked_tier_names = []
        for tier in existing_tiers:
            order_count = session.exec(
                select(func.count(Order.id)).where(Order.ticket_tier_id == tier.id)
            ).one()
            if order_count == 0:
                session.delete(tier)
            else:
                locked_tier_names.append(tier.category_name)

        session.flush()

        new_tiers = []
        for tier_data in event_data.ticket_tiers:
            if tier_data.category_name in locked_tier_names:
                continue  
            new_tier = TicketTier(
                event_id=id,
                category_name=tier_data.category_name,
                price=tier_data.price,
                currency=tier_data.currency,
                total_seats=tier_data.total_seats,
                benefits_included=tier_data.benefits_included,
                description=tier_data.description
            )
            session.add(new_tier)
            new_tiers.append(new_tier)

    session.flush()
    session.refresh(event)
    for t in new_tiers:
        session.refresh(t)

    all_tiers = session.exec(select(TicketTier).where(TicketTier.event_id == id)).all()
    return {"event": event, "ticket_tiers": all_tiers}


def get_fraud_orders(user: User, session: Session):
    if user.role != "organizer":
        raise Forbidden()
    events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    event_ids = [e.id for e in events]

    flagged = session.exec(
        select(Order).where(Order.event_id.in_(event_ids), Order.status == "fraud_review")
    ).all() if event_ids else []

    result = []
    for order in flagged:
        customer = session.get(User, order.user_id)
        event = session.get(Event, order.event_id)
        tier = session.get(TicketTier, order.ticket_tier_id)
        result.append({
            "id": order.id,
            "userName": customer.full_name if customer else "Unknown",
            "email": customer.email if customer else "",
            "eventName": event.name if event else "Unknown",
            "bookingDate": order.created_at.isoformat() if order.created_at else "",
            "reason": "Flagged by fraud detection model",
            "riskScore": 75,
            "status": "flagged",
        })
    return result