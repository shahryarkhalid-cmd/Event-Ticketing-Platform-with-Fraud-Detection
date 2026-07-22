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
