from fastapi import Depends
from sqlmodel import Session , select
from models.Event import EventCreate , Event
from models.Users import User
import logging
from dependencies.exception import Forbidden ,Event_Not_Found
def Make_Event( event : EventCreate , user : User , session : Session):
    user_info = session.exec(select(User).where(User.email == user.email)).first()
    if user_info.role != "organizer":
        logging.error("User is not Organizer!")
        raise Forbidden()
    final_event = Event(name = event.name , description = event.description , venue=event.venue , date = event.date , organizer_id=user_info.id)
    session.add(final_event)
    session.flush()
    session.refresh(final_event)
    logging.info("Event has been created")
    return final_event


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
    session.delete(to_delete)
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