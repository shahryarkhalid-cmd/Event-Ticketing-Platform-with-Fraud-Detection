import pytest 
from conftest import client
from models.Users import User , UserRole
from sqlmodel import select
EVENT = {
                "name": "Musical Night",
                "category": "other",
                "description": "Music with Farhad",
                "venue": "Expo Center",
                "address": "123 Main Street",
                "city": "Lahore",
                "country": "Pakistan",
                "start_datetime": "2024-08-01T19:00:00",
                "end_datetime": "2024-08-01T23:00:00",
                "max_capacity": 100,
                "dress_code": "formal",
                "age_restriction": 50,
                "parking_available": False,
                "food_available": True,
                "refund_policy": "Full refund within 1 days",
                "terms_accepted": True,
                "ticket_tiers": [
                    {
                        "category_name": "VIP",
                        "price": 3000,
                        "currency": "USD",
                        "total_seats": 50,
                        "benefits_included": "Front row, meet & greet",
                        "description": "Best seats in the house"
                    },
                    {
                        "category_name": "General",
                        "price": 1500,
                        "currency": "PKR",
                        "total_seats": 450,
                        "benefits_included": None,
                        "description": "Standard entry"
                    }
                ]
            }

EVENT_2 ={
            "name": "Tekken Event",
            "category": "gaming",
            "description": "The Tekken 8 event",
            "venue": "Expo Center",
            "address": "123 Main Street",
            "city": "Lahore",
            "country": "Pakistan",
            "start_datetime": "2026-08-01T19:00:00",
            "end_datetime": "2026-08-01T23:00:00",
            "max_capacity": 500,
            "dress_code": "Casual",
            "age_restriction": 13,
            "parking_available": True,
            "food_available": True,
            "refund_policy": "Full refund within 7 days",
            "terms_accepted": True,
            "ticket_tiers": [
                {
                    "category_name": "VIP",
                    "price": 5000,
                    "currency": "PKR",
                    "total_seats": 50,
                    "benefits_included": "Front row, meet & greet",
                    "description": "Best seats in the house"
                },
                {
                    "category_name": "General",
                    "price": 1500,
                    "currency": "PKR",
                    "total_seats": 450,
                    "benefits_included": None,
                    "description": "Standard entry"
                }
            ]
        }
def test_event(client):
    client.post('/auth/register', json={
        'email': 'sherrykhalid86@gmail.com',
        'full_name': 'shahryar',
        'password': '12345',
        'role' : 'organizer'
    })
    login_ = client.post('/auth/login', json={
        'email': 'sherrykhalid86@gmail.com',
        'password': '12345'
    })
    header_1 = login_.json()['access_token']

    event_payload = EVENT_2

    response = client.post(
        '/publish-event',
        json=event_payload,
        headers={"Authorization": f'Bearer {header_1}'}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["event"]["name"] == "Tekken Event"
    assert len(data["ticket_tiers"]) == 2
    assert data["ticket_tiers"][0]["category_name"] == "VIP"
    
def test_Get_List_Event(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345' , 'role' : 'organizer'})
    client.post('/auth/register' , json={'email' : 'ahmed12@gmail.com' , 'full_name' : 'ahmed' , 'password' : '123455' , 'role' : 'organizer'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid@gmail.com' , 'password': '12345'})
    login_2 = client.post('/auth/login',  json = {'email' : 'ahmed12@gmail.com' , 'password' : '123455'})
    header_1 = login_.json()['access_token']
    header_2 = login_2.json()['access_token']
    event_1 = EVENT_2
    event_2 = EVENT
    client.post("/make_event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    create_response = client.post("/publish-event", json = event_1 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    print(create_response.json())
    assert create_response.status_code == 200
    response = client.get('/get_all_events' , headers ={"Authorization" : f'Bearer {header_1}'})
    assert response.status_code == 200
    
def test_get_event_specific_id(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345', 'role' : 'organizer'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    event_2 = EVENT
    create_response = client.post("/publish-event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    print(create_response.json())
    assert create_response.status_code == 200
    event_id = create_response.json()["event"]["id"]
    response = client.get(f"/get_event/{event_id}" , headers={"Authorization": f'Bearer {header_1}'})
    assert response.status_code == 200
    assert response.json()["id"] == event_id
    assert response.json()["name"] == "Musical Night"
    
    
def test_delete_event(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345' , 'role' : 'organizer'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    event_2 = EVENT
    create_response = client.post("/publish-event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    assert create_response.status_code == 200
    response = client.delete('/delete_all_event' , headers={"Authorization": f'Bearer {header_1}'})
    assert response.status_code == 200
    
    
def test_delete_specific_event(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345' , 'role':'organizer'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    event_2 = EVENT
    create_response = client.post("/publish-event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    assert create_response.status_code == 200
    event_id = create_response.json()['event']['id']
    response = client.delete(f'/delete_event/{event_id}' , headers = {"Authorization" : f'Bearer {header_1}'})
    data = response.json()
    assert response.status_code == 200
    assert data['message'] == "Deleted sucessfully"
    
    
def test_ticket_system(client):
    client.post('/auth/register' , json={'email' : 'sherrykhalid86@gmail.com' , 'full_name' : 'shahryar' , 'password' : '12345' , 'role' : 'organizer'})
    login_ = client.post('/auth/login',  json = {'email' : 'sherrykhalid86@gmail.com' , 'password': '12345'})
    header_1 = login_.json()['access_token']
    event_2 = EVENT
    create_response = client.post("/publish-event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    assert create_response.status_code == 200
    event_id = create_response.json()['event']['id']
    response = client.get(f'/events/{event_id}/ticket-tiers' , headers={"Authorization" : f"Bearer {header_1}"})
    data = response.json()
    print(data)
    assert response.status_code == 200
    assert data[0]["category_name"] ==  'VIP'

# testing customer window 
def test_search_events(client):
    client.post('/auth/register', json={
        'email': 'sherrykhalid86@gmail.com',
        'full_name': 'shahryar',
        'password': '12345' ,
        'role' : 'organizer'
    })
    login_ = client.post('/auth/login', json={
        'email': 'sherrykhalid86@gmail.com',
        'password': '12345'
    })
    header_1 = login_.json()['access_token']

    create_response = client.post(
        "/publish-event",
        json=EVENT,
        headers={"Authorization": f'Bearer {header_1}'}
    )
    assert create_response.status_code == 200

    response = client.get("/events/customer")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    response = client.get("/events/customer", params={"search": "Musical"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Musical" in e["name"] for e in data)

    response = client.get("/events/customer", params={"city": "Lahore"})
    assert response.status_code == 200
    data = response.json()
    assert all(e["city"] == "Lahore" for e in data)

    response = client.get("/events/customer", params={"country": "Pakistan"})
    assert response.status_code == 200
    data = response.json()
    assert all(e["country"] == "Pakistan" for e in data)

    response = client.get("/events/customer", params={"city": "Lahore", "category": "other"})
    assert response.status_code == 200
    data = response.json()
    assert all(e["city"] == "Lahore" and e["category"] == "other" for e in data)

    response = client.get("/events/customer", params={"city": "NoSuchCityXYZ"})
    assert response.status_code == 200
    data = response.json()
    assert data == []
    
    
# testing the order placement :
from models.Orders import CartItem
def test_book_ticket(client):
    client.post('/auth/register', json={'email': 'organizer@test.com', 'full_name': 'Org', 'password': '12345' , 'role' : 'organizer'})
    org_login = client.post('/auth/login', json={'email': 'organizer@test.com', 'password': '12345'})
    org_headers = {"Authorization": f'Bearer {org_login.json()["access_token"]}'}

    create_response = client.post("/publish-event", json=EVENT, headers=org_headers)
    assert create_response.status_code == 200
    event_id = create_response.json()['event']['id']

    client.post('/auth/register', json={'email': 'customer@test.com', 'full_name': 'Cust', 'password': '12345' , 'role' : 'customer'})
    
    cust_login = client.post('/auth/login', json={'email': 'customer@test.com', 'password': '12345'})
    cust_headers = {"Authorization": f'Bearer {cust_login.json()["access_token"]}'}
    cart_item = []
    for cart in range(2):
        tier_id = create_response.json()['ticket_tiers'][cart]['id']
        items = CartItem(quantity= cart + 10 , ticket_tier_id=tier_id)
        cart_item.append(items.model_dump())
        
    order_response = client.post("/orders", json={"event_id": event_id, "items": cart_item}, headers=cust_headers)
    assert order_response.status_code == 200
