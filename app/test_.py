import pytest 
from services.Organizer_services import Make_Event
from conftest import client

def test_event(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    response = client.post('/make_event' , json= {"name" : "Tekken event" , "description" : "The Tekken 8 event" , "venue" : "Lahore" , "date" : "2024-03-02"} , headers ={"Authorization" : f'Bearer {header_1}'})
    assert response.json() == {"message": "Event has been created"}
    