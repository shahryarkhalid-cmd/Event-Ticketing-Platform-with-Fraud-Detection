from models.Users import User
from models.Notification import Notification
from sqlmodel import Session , select
from fastapi import HTTPException
def get_notifications(user: User, session: Session):
    notifications =  session.exec(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    ).all()
    return notifications

def mark_notification_read(notification_id: int, user: User, session: Session):
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    session.add(notification)
    session.flush()
    return notification

def delete_notification(user : User , session : Session):
    notification = session.exec(select(Notification).where(Notification.user_id == user.id)).all()
    for single_note in notification:
        session.delete(single_note)
    session.flush() 
    return {'detail': 'Notification Deleted sucessfully!'}
    
    