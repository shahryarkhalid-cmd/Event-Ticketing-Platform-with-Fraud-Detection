import pytest 
from conftest import client


def test_event(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    response = client.post('/make_event' , json= {"name" : "Tekken event" , "description" : "The Tekken 8 event" , "venue" : "Lahore" , "date" : "2024-03-02"} , headers ={"Authorization" : f'Bearer {header_1}'})
    assert response.status_code == 200
    
def test_Get_List_Event(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345'})
    client.post('/auth/register' , json={'email' : 'ahmed12@gmail.com' , 'full_name' : 'ahmed' , 'password' : '123455'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    login_2 = client.post('/auth/login',  json = {'email' : 'ahmed12@gmail.com' , 'password' : '123455'})
    header_1 = login_.json()['access_token']
    header_2 = login_2.json()['access_token']
    event_1 = client.post('/make_event' , json= {"name" : "Tekken event" , "description" : "The Tekken 8 event" , "venue" : "Lahore" , "date" : "2024-03-02"} , headers ={"Authorization" : f'Bearer {header_1}'})
    event_2 = client.post('/make_event' , json= {"name" : "FIFA EVENT" , "description" : "The FIFA event" , "venue" : "ISL" , "date" : "2026-04-08"} , headers ={"Authorization" : f'Bearer {header_1}'})
    response = client.get('/get_all_events' , headers ={"Authorization" : f'Bearer {header_1}'})
    assert response.status_code == 200
    
def test_get_event_specific_id(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    event_data = {
        "name": "Music Night",
        "description": "A great concert",
        "venue": "City Hall",
        "date": "2026-08-01T19:00:00"
    }
    create_response = client.post("/make_event", json = event_data ,  headers ={"Authorization" : f'Bearer {header_1}'})
    print(create_response.json())
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    response = client.get(f"/get_event/{event_id}" , headers={"Authorization": f'Bearer {header_1}'})
    assert response.status_code == 200
    assert response.json()["id"] == event_id
    assert response.json()["name"] == "Music Night"