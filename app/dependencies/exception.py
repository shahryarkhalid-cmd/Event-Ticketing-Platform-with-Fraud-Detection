class Email_exist(Exception):
    pass

class User_Exist(Exception):
    pass

class password_mismatch(Exception):
    pass

class Email_registration(Exception):
    pass

class Forbidden(Exception):
    pass

class Event_Not_Found(Exception):
    pass

class Not_customer(Exception):
    pass

class Ticket_Tier_not_found(Exception):
    pass


class Order_Quantity_Error(Exception):
    pass

class Not_Enough_Tickets(Exception):
    pass

class BookingContention(Exception):

    pass

class Not_Order(Exception):

    pass

class Order_Mismatch(Exception):

    pass


class Not_Pending_Order(Exception):

    pass

class Not_Your_Event(Exception):
    
    
    pass

class Paid_Refund(Exception):
    
    pass
    
    
from fastapi.responses import JSONResponse

from fastapi import Request

def email_existing(req : Request , exec : Email_exist):
    return JSONResponse(status_code=409 , content= {"detail" :  "Email already exists."})

def user_existence(req : Request , exec : User_Exist):
    return JSONResponse(status_code=409 , content = {"detail" : "User already exist."})

def incorrect_password(req : Request , exec : password_mismatch):
    return JSONResponse(status_code=400 , content= {"detail" :  "Password Mismatched"})

def email_reg(req : Request , exec : Email_registration):
    
    return JSONResponse(status_code = 404 , content = {"detail" :  "Email or password is incorrect."})

def forbidden(req : Request , exec : Forbidden):
    return JSONResponse(status_code=403 , content={"detail" : "Forbidden"})

def event_not_found(req : Request , exec : Event_Not_Found):
    return JSONResponse(status_code=404 , content = {"detail" : "Event not found"})

def not_customer(req : Request , exec : Not_customer):
    return JSONResponse(status_code=404 , content = {'detail' : 'Not Customer'})

def no_ticket_tier(req : Request , exec : Ticket_Tier_not_found):
    return JSONResponse(status_code=404 , content = {"detail" : "No Ticket Tier Found"})

def less_order_quantity(req : Request , exec : Order_Quantity_Error):
    return JSONResponse(status_code=400 , content= {"detail" : "Quantity must be at least 1"})

def not_enough_tickets(req : Request , exec : Not_Enough_Tickets):
    return JSONResponse(status_code=409 , content={"detail" : "Not enough tickets avalaible"})

def booking_contention(req : Request , exec : BookingContention):
    return JSONResponse(status_code=409, content={"detail": "High demand right now, please try again"})

def not_order(req : Request , exec : Not_Order):
    return JSONResponse(status_code = 404 , content={"detail" : "Order not found"})

def order_mismatch(req : Request , exec : Order_Mismatch):
    return JSONResponse(status_code=409 , content={'detail': 'This is not your oder'})

def not_pending_order(req : Request , exec : Not_Pending_Order):
    return JSONResponse(status_code=400 , content = {"detail" : "Order is not pending"})

def not_your_event(req : Request , exec : Not_Your_Event):
    return JSONResponse(status_code=403 , content = {"detail" : "Not your event"})

def paid_refund(req : Request , exec : Paid_Refund):
    return JSONResponse(status_code=403 , content = {'detail' : 'Only paid event can be refunded'})
