from fastapi import Depends
from sqlmodel import Session , select
from models.Event import EventCreate , Event
from models.Users import User
import logging
from dependencies.exception import Forbidden
def Make_Event( event : EventCreate , user : User , session : Session):
    user_info = session.exec(select(User).where(User.email == user.email)).first()
    if user_info.role != "organizer":
        logging.error("User is not Organizer!")
        raise Forbidden()
    final_event = Event(name = event.name , description = event.description , venue=event.description , date = event.date , organizer_id=user_info.id)
    session.add(final_event)
    logging.info("Event has been created")
    return {"message" : "Event has been created"}


def get_organizer_events(user : User , session : Session):
    if user.role != "organizer":
        logging.error("User is not the organizer")
        raise Forbidden()
 
    listed_events = session.exec(select(Event).where(Event.organizer_id == user.id)).all()
    return listed_events
    