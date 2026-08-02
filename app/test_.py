import pytest 
import uuid
from conftest import client
from models.Users import User , UserRole
from sqlmodel import select
from models.Orders import CartItem


class AuthHeader(dict):
    def __init__(self, token: str):
        super().__init__({"Authorization": f"Bearer {token}"})
        self.token = token

    def __str__(self):
        return self.token

    def __repr__(self):
        return self.token
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
                        "price": 10,
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


import core.redis_client as redis_module

import services.Verification_service as verification_module

def register_and_login(client, email, full_name, password, role):
    resolved_email = email
    resolved_full_name = full_name
    register_response = None

    for _ in range(5):
        register_response = client.post('/auth/register', json={
            'email': resolved_email, 'full_name': resolved_full_name, 'password': password, 'role': role
        })
        if register_response.status_code == 200:
            break

        payload = register_response.json()
        if register_response.status_code in {400, 409} and isinstance(payload, dict):
            detail = str(payload).lower()
            if 'already' in detail or 'exist' in detail or 'registered' in detail:
                local_part, domain = resolved_email.split('@', 1)
                resolved_email = f"{local_part}+{uuid.uuid4().hex[:8]}@{domain}"
                resolved_full_name = f"{full_name}-{uuid.uuid4().hex[:8]}"
                continue

        assert register_response.status_code == 200, f"Registration failed: {payload}"

    assert register_response.status_code == 200, f"Registration failed: {register_response.json()}"

    code = verification_module.redis_client.get(f"email_verify:{resolved_email}")
    assert code is not None, f"No OTP found in Redis for {resolved_email}"

    verify_response = client.post('/auth/verify-email', json={'email': resolved_email, 'code': code})
    assert verify_response.status_code == 200, f"Email verification failed: {verify_response.json()}"

    login_ = client.post('/auth/login', json={'email': resolved_email, 'password': password})
    assert login_.status_code == 200, f"Login failed: {login_.json()}"
    token = login_.json()['access_token']
    return AuthHeader(token)

def test_event(client):
    header_1 = register_and_login(client, "test_event@gmail.com", "shahryar", "123", "organizer")

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
    header_1 = register_and_login(client, "get_list@gmail.com", "shahryar", "123", "organizer")
    header_2 = register_and_login(client, "get_list_2@gmail.com", "shahryar23", "1234", "organizer")
    event_1 = EVENT_2
    event_2 = EVENT
    client.post("/make_event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    create_response = client.post("/publish-event", json = event_1 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    print(create_response.json())
    assert create_response.status_code == 200
    response = client.get('/get_all_events' , headers ={"Authorization" : f'Bearer {header_1}'})
    assert response.status_code == 200
    
def test_get_event_specific_id(client):
    header_1 = register_and_login(client, "specific_id@gmail.com", "shahryar", "123", "organizer")
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
    header_1 = register_and_login(client, "delete_event@gmail.com", "shahryar", "123", "organizer")
    event_2 = EVENT
    create_response = client.post("/publish-event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    assert create_response.status_code == 200
    response = client.delete('/delete_all_event' , headers={"Authorization": f'Bearer {header_1}'})
    assert response.status_code == 200
    
    
def test_delete_specific_event(client):
    header_1 = register_and_login(client, "delete_specific@gmail.com", "shahryar", "123", "organizer")
    event_2 = EVENT
    create_response = client.post("/publish-event", json = event_2 ,  headers ={"Authorization" : f'Bearer {header_1}'})
    assert create_response.status_code == 200
    event_id = create_response.json()['event']['id']
    response = client.delete(f'/delete_event/{event_id}' , headers = {"Authorization" : f'Bearer {header_1}'})
    data = response.json()
    assert response.status_code == 200
    assert data['message'] == "Deleted sucessfully"
    
    
def test_ticket_system(client):
    header_1 = register_and_login(client, "ticket_system@gmail.com", "shahryar", "123", "organizer")
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
    header_1 = register_and_login(client, "test_search@gmail.com", "shahryar", "123", "organizer")

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
# Testing the dashboard graphs of the Organizer Window:
from models.Orders import Order
def test_get_analytics_summary(client , test_session):
    header_1 = register_and_login(client, "get_analytics@gmail.com", "shahryar", "123", "organizer")
    header={"Authorization": f'Bearer {header_1}'}
    
    create_response = client.post('/publish-event' , json=EVENT , headers = header)
    event_id = create_response.json()['event']['id']
    header_2 = register_and_login(client, "shahryarkhalid8@gmail.com", "shan", "123", "customer")
    header_customer ={"Authorization": f'Bearer {header_2}'}
    
    cart_item = []
    for cart in range(2):
            tier_id = create_response.json()['ticket_tiers'][cart]['id']
            items = CartItem(quantity= cart + 10 , ticket_tier_id=tier_id)
            cart_item.append(items.model_dump())
            
            
    order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
    assert order_response.status_code == 200
    order_id = order_response.json()['id']
    order = test_session.get(Order, int(order_id))
    order.payment_status = "paid"
    test_session.add(order)
    test_session.commit()
    
    
    response = client.get("/organizer/analytics/summary" , headers=header)
    assert response.status_code == 200
    
    
 
def test_get_ticket_sales(client , test_session):
            header_1 = register_and_login(client, "get_ticket_sales@gmail.com", "shahryar", "123", "organizer")
            header={"Authorization": f'Bearer {header_1}'}
            
            create_response = client.post('/publish-event' , json=EVENT , headers = header)
            event_id = create_response.json()['event']['id']
            header_2 = register_and_login(client, "shahryarkhalid8@gmail.com", "shahrya12r", "123", "customer")
            header_customer ={"Authorization": f'Bearer {header_2}'}
            
            cart_item = []
            for cart in range(2):
                    tier_id = create_response.json()['ticket_tiers'][cart]['id']
                    items = CartItem(quantity= 10 , ticket_tier_id=tier_id)
                    cart_item.append(items.model_dump())
                    
                    
            order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
            assert order_response.status_code == 200
            order_id = order_response.json()['id']
            order = test_session.get(Order, int(order_id))
            order.payment_status = "paid"
            test_session.add(order)
            test_session.commit()
            response = client.get('/organizer/analytics/ticket-sales' , headers = header)
            day = order.created_at.strftime("%a")
            assert response.status_code == 200
            assert response.json()[day] == 20
            
    
def test_get_ticket_popularity(client , test_session):
        header_1 = register_and_login(client, "test_get_popularity@gmail.com", "shahryar", "123", "organizer")
        header={"Authorization": f'Bearer {header_1}'}
        
        create_response = client.post('/publish-event' , json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        header_2 = register_and_login(client, "shahryarkhali6@gmail.com", "ali", "1213", "customer")
        header_customer ={"Authorization": f'Bearer {header_2}'}
        
        cart_item = []
        for cart in range(2):
                tier_id = create_response.json()['ticket_tiers'][cart]['id']
                tier_name = create_response.json()['ticket_tiers'][cart]['category_name']
                if tier_name == "General":
                    quantity = 100 ;
                if tier_name == "VIP":
                    quantity = 10 ;
                items = CartItem(quantity = quantity , ticket_tier_id=tier_id)
                cart_item.append(items.model_dump())
                
                
        order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
        assert order_response.status_code == 200
        order_id = order_response.json()['id']
        order = test_session.get(Order, int(order_id))
        order.payment_status = "paid"
        test_session.add(order)
        test_session.commit()
        
        assert order_response.status_code == 200
        order_id = order_response.json()['id']
        order = test_session.get(Order, int(order_id))
        order.payment_status = "paid"
        test_session.add(order)
        test_session.commit()
        response = client.get("/organizer/analytics/popular-categories" , headers=header)
        assert response.status_code == 200
        assert response.json()["VIP"] == 10
        
        
# testing the booking status : 
def test_booking_status(client , test_session):
        header_1 = register_and_login(client, "get_booking_status@gmail.com", "shahryar", "123", "organizer")
        header={"Authorization": f'Bearer {header_1}'}
        
        create_response = client.post('/publish-event' , json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        customer_email = "shahryar8@gmail.com"
        header_2 = register_and_login(client, customer_email, "customer", "1233", "customer")
        header_customer ={"Authorization": f'Bearer {header_2}'}
        
        cart_item = []
        for cart in range(2):
                tier_id = create_response.json()['ticket_tiers'][cart]['id']
                tier_name = create_response.json()['ticket_tiers'][cart]['category_name']
                if tier_name == "General":
                    quantity = 100 ;
                if tier_name == "VIP":
                    quantity = 10 ;
                items = CartItem(quantity = quantity , ticket_tier_id=tier_id)
                cart_item.append(items.model_dump())
                
                
        order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
        assert order_response.status_code == 200
        order_id = order_response.json()['id']
        order = test_session.get(Order, int(order_id))
        order.payment_status = "paid"
        test_session.add(order)
        test_session.commit()
        response = client.get('/organizer/bookings' , headers = header)
        data = response.json()
        vip_item = next(d for d in data if d['category'] == 'VIP')
        general_item = next(d for d in data if d['category'] == 'General')

        assert vip_item['customer'] == 'customer'
        assert vip_item['email'] == customer_email
        assert vip_item['event'] == create_response.json()['event']['name']
        assert vip_item['qty'] == 10
        assert vip_item['qr_generated'] == False
        


# Testing revenue :

def test_revenue(client , test_session):
    
        header_1 = register_and_login(client, "test_revenue@gmail.com", "shahryar", "123", "organizer")
        header={"Authorization": f'Bearer {header_1}'}
        
        create_response = client.post('/publish-event' , json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        header_2 = register_and_login(client, "test_revenue_2@gmail.com", "shahrar", "123", "customer")
        header_customer ={"Authorization": f'Bearer {header_2}'}
        
        cart_item = []
        for cart in range(2):
                tier_id = create_response.json()['ticket_tiers'][cart]['id']
                tier_name = create_response.json()['ticket_tiers'][cart]['category_name']
                if tier_name == "General":
                    quantity = 1 ;
                if tier_name == "VIP":
                    quantity = 1 ;
                items = CartItem(quantity = quantity , ticket_tier_id=tier_id)
                cart_item.append(items.model_dump())
                
                
        order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
        assert order_response.status_code == 200
        order_id = order_response.json()['id']
        order = test_session.get(Order, int(order_id))
        order.payment_status = "paid"
        test_session.add(order)
        test_session.commit()
        response = client.get('/organizer/revenue/overview' , headers = header) 
        data = response.json()
        
        assert response.status_code == 200
        assert data['total_revenue'] == 1510
        assert data['refunded'] == 0
        

# tesing monthly revenue trend:
def test_monthly_revenue_trend(client , test_session):
            header_1 = register_and_login(client, "monthly_revenue_00@gmail.com", "shahryar", "123", "organizer")
            header={"Authorization": f'Bearer {header_1}'}
            
            create_response = client.post('/publish-event' , json=EVENT , headers = header)
            event_id = create_response.json()['event']['id']
            header_2 = register_and_login(client, "monthly_revenue_01@gmail.com", "shah2ryar", "1123", "customer")
            header_customer ={"Authorization": f'Bearer {header_2}'}
            
            cart_item = []
            for cart in range(2):
                    tier_id = create_response.json()['ticket_tiers'][cart]['id']
                    tier_name = create_response.json()['ticket_tiers'][cart]['category_name']
                    if tier_name == "General":
                        quantity = 1 ;
                    if tier_name == "VIP":
                        quantity = 1 ;
                    items = CartItem(quantity = quantity , ticket_tier_id=tier_id)
                    cart_item.append(items.model_dump())
                    
                    
            order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
            assert order_response.status_code == 200
            order_id = order_response.json()['id']
            order = test_session.get(Order, int(order_id))
            order.payment_status = "paid"
            test_session.add(order)
            test_session.commit()
            response = client.get('/organizer/revenue/trend' , headers = header)
            month = order.created_at.strftime("%b")
            assert response.status_code ==200
            assert response.json()[month] == 1510
# testing the refund system:
def test_refund(client , test_session):
            header_1 = register_and_login(client, "test_refund_2000@gmail.com", "shahryar", "123", "organizer")
            header={"Authorization": f'Bearer {header_1}'}
            
            create_response = client.post('/publish-event' , json=EVENT , headers = header)
            event_id = create_response.json()['event']['id']
            header_2 = register_and_login(client, "shahry0098@gmail.com", "ali", "12e3", "customer")
            header_customer ={"Authorization": f'Bearer {header_2}'}
            
            cart_item = []
            for cart in range(2):
                    tier_id = create_response.json()['ticket_tiers'][cart]['id']
                    tier_name = create_response.json()['ticket_tiers'][cart]['category_name']
                    if tier_name == "General":
                        quantity = 1 ;
                    if tier_name == "VIP":
                        quantity = 1 ;
                    items = CartItem(quantity = quantity , ticket_tier_id=tier_id)
                    cart_item.append(items.model_dump())
                    
                    
            order_response =client.post('/orders' , json = {'event_id' :event_id , 'items' : cart_item} , headers = header_customer)
            assert order_response.status_code == 200
            order_id = order_response.json()['id']
            order = test_session.get(Order, int(order_id))
            order.payment_status = "paid"
            test_session.add(order)
            test_session.commit()
            response = client.post(f'/organizer/orders/{int(order_id)}/refund' , headers = header)
            assert response.status_code == 200 
            data = response.json()
            assert data['payment_status'] == 'refunded'
    
# testing the order placement :
def test_book_ticket(client):
    header_1 = register_and_login(client, "test_book_ticket@gmail.com", "shahryar", "123", "organizer")
    org_headers = {"Authorization": f'Bearer {header_1}'}

    create_response = client.post("/publish-event", json=EVENT, headers=org_headers)
    assert create_response.status_code == 200
    event_id = create_response.json()['event']['id']

    header_2 = register_and_login(client, "shahryarkhalid826@gmail.com", "shahry2ar", "1223", "customer")
    cust_headers = {"Authorization": f'Bearer {header_2}'}
    cart_item = []
    for cart in range(2):
        tier_id = create_response.json()['ticket_tiers'][cart]['id']
        items = CartItem(quantity= cart + 10 , ticket_tier_id=tier_id)
        cart_item.append(items.model_dump())
        
    order_response = client.post("/orders", json={"event_id": event_id, "items": cart_item}, headers=cust_headers)
    assert order_response.status_code == 200
def test_update_event(client):
        header_1 = register_and_login(client, "test_update_event@gmail.com", "shahryar", "123", "organizer")
        header={"Authorization": f'Bearer {header_1}'}
            
        create_response = client.post('/publish-event' ,json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        response = client.put(f'/update_event/{event_id}', json =EVENT_2, headers = header)
        assert response.status_code == 200
        assert response.json()['event']['name'] == 'Tekken Event'
        
        
        
# Testing customer Routes :
from models.Orders import Order
def setup_event_with_tiers(client, org_header):
    create_response = client.post('/publish-event', json=EVENT, headers=org_header)
    assert create_response.status_code == 200
    return create_response.json()


# ---------- POST /orders ----------

def test_create_order_success(client):
    org_header ={"Authorization": f'Bearer {register_and_login(client, 'org1@test.com', 'Org', 'pass123', 'organizer')}'} 
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust1@test.com', 'Cust', 'pass123', 'customer')

    response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 2}]
    }, headers=cust_header)

    assert response.status_code == 200
    data = response.json()
    assert data['event_id'] == event_id
    assert data['payment_status'] == 'pending'


def test_create_order_requires_customer_role(client):
    org_header ={"Authorization": f'Bearer {register_and_login(client, 'org2@test.com', 'Org', 'pass123', 'organizer')}'} 
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    # Organizer tries to book their own event
    response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=org_header)

    assert response.status_code == 404


def test_create_order_not_enough_tickets(client):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'org3@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust3@test.com', 'Cust', 'pass123', 'customer')

    response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 999999}]
    }, headers=cust_header)

    assert response.status_code == 409


# ---------- GET /orders/me ----------

def test_get_my_orders(client):
    
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'org4@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'cust4@test.com', 'Cust', 'pass123', 'customer')}'}
    client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)

    response = client.get('/orders/me', headers=cust_header)
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) >= 1
    assert orders[0]['event_id'] == event_id


def test_get_my_orders_empty_for_new_user(client):
    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'cust5@test.com', 'Cust', 'pass123', 'customer')}'}
    
    response = client.get('/orders/me', headers=cust_header)
    assert response.status_code == 200
    assert response.json() == []


# ---------- GET /orders/{order_id} ----------

def test_get_order_status(client):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'org6@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust6@test.com', 'Cust', 'pass123', 'customer')

    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    response = client.get(f'/orders/{order_id}', headers=cust_header)
    assert response.status_code == 200
    assert response.json()['id'] == order_id
    assert response.json()['payment_status'] == 'pending'


def test_get_order_status_wrong_user_forbidden(client):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'org7@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'cust7@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    # A different customer tries to view someone else's order
    other_header = register_and_login(client, 'cust8@test.com', 'Cust2', 'pass123', 'customer')
    response = client.get(f'/orders/{order_id}', headers=other_header)
    assert response.status_code == 403


def test_get_order_status_not_found(client):
    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'cust7@test.com', 'Cust', 'pass123', 'customer')}'}
    response = client.get('/orders/999999', headers=cust_header)
    assert response.status_code == 404


# ---------- POST /orders/{order_id}/checkout ----------

def test_create_checkout_session(client):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'cust7@test.com', 'Cust', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'cust10@test.com', 'Cust', 'pass123', 'customer')}'}
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    response = client.post(f'/orders/{order_id}/checkout', headers=cust_header)
    assert response.status_code == 200
    assert "checkout_url" in response.json()


def test_checkout_wrong_user_forbidden(client):
    org_header =  {"Authorization": f'Bearer {register_and_login(client, 'org11@test.com', 'Org', 'pass123', 'organizer')}'}
   
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'cust11@test.com', 'Cust', 'pass123', 'customer')}'}
     
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    other_header = {"Authorization": f'Bearer {register_and_login(client, 'cust12@test.com', 'Cust2', 'pass123', 'customer')}'}
    
    response = client.post(f'/orders/{order_id}/checkout', headers=other_header)
    assert response.status_code == 409


def test_checkout_non_pending_order_rejected(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'org13@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer { register_and_login(client, 'cust13@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    order = test_session.get(Order, order_id)
    order.payment_status = "paid"
    test_session.add(order)
    test_session.commit()

    response = client.post(f'/orders/{order_id}/checkout', headers=cust_header)
    assert response.status_code == 400
    
    
    
# Testing the stripe checkout , Webhook Actually updates the order:
from unittest.mock import patch
from models.Orders import Order


def make_fake_stripe_event(order_id: int):
    return {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"order_id": str(order_id)}
            }
        }
    }


def test_stripe_webhook_marks_order_as_paid(client, test_session):
    # 1. Set up a normal order, same as always
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgwh@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custwh@test.com', 'Cust', 'pass123', 'customer')}'}
   
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    order = test_session.get(Order, order_id)
    assert order.payment_status == "pending"

    fake_event = make_fake_stripe_event(order_id)
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        response = client.post(
            "/webhooks/stripe",
            data=b"irrelevant-fake-payload",
            headers={"stripe-signature": "fake-signature-for-test"}
        )

    assert response.status_code == 200
    test_session.refresh(order)
    assert order.payment_status == "paid"
            


# ============= TESTING FRAUD DETECTION SERVICES AND ROUTES ====================

def test_fraud_detection_pipeline_integration(client, test_session, caplog):
    import logging
    caplog.set_level(logging.INFO)

    from sqlmodel import select
    from models.Users import User, UserRole
    from models.Orders import Order, OrderItem

    # ── 1. Organizer registration & event creation ──
    org_headers = {"Authorization": f"Bearer {register_and_login(client, 'org_fraud_test@test.com', 'Org Fraud', 'pass123', 'organizer')}"}

    event_resp = client.post("/publish-event", json=EVENT, headers=org_headers)
    assert event_resp.status_code == 200
    tier_id = event_resp.json()['ticket_tiers'][0]['id']
    event_id = event_resp.json()['event']['id']

    # ── 2. Customer registration & role assignment ──
    cust_headers = {"Authorization": f"Bearer {register_and_login(client, 'cust_fraud_test@test.com', 'Cust Fraud', 'pass123', 'customer')}"}

    # ── 3. Place order — fraud detection pipeline executes ──
    order_resp = client.post(
        "/orders",
        json={"event_id": event_id, "items": [{"ticket_tier_id": tier_id, "quantity": 2}]},
        headers=cust_headers,
    )
    assert order_resp.status_code == 200
    order = order_resp.json()

    # ── 4. Verify order response schema ──
    expected_order_fields = {"id", "user_id", "event_id", "total_price", "payment_status", "fraud_status", "created_at"}
    assert expected_order_fields.issubset(order.keys()), f"Missing order fields: {expected_order_fields - order.keys()}"
    assert order["payment_status"] == "pending", f"Unexpected payment status: {order['payment_status']}"
    assert order["fraud_status"] in (None, "fraud_review"), f"Unexpected fraud status: {order['fraud_status']}"
    assert order["total_price"] > 0

    # ── 5. Verify fraud detection code actually executed ──
    assert any("Fraud prediction" in r.message for r in caplog.records), \
        "Fraud prediction log not found — pipeline did not execute"
    assert any("Fraud model loaded" in r.message for r in caplog.records), \
        "Model loading log not found"
    assert any("Prediction complete" in r.message for r in caplog.records), \
        "Prediction completion log not found"

    # ── 6. Verify database state matches API ──
    db_order = test_session.get(Order, order["id"])
    assert db_order is not None
    assert db_order.payment_status == order["payment_status"]
    assert db_order.fraud_status == order["fraud_status"]
    assert db_order.total_price == order["total_price"]
    assert db_order.event_id == event_id

    order_items = test_session.exec(select(OrderItem).where(OrderItem.order_id == db_order.id)).all()
    total_quantity = sum(i.quantity for i in order_items)
    assert total_quantity == 2

    # ── 7. Verify organizer fraud endpoint ──
    fraud_resp = client.get("/organizer/fraud-orders", headers=org_headers)
    assert fraud_resp.status_code == 200
    fraud_orders = fraud_resp.json()
    assert isinstance(fraud_orders, list)

    expected_fraud_fields = {"id", "userName", "email", "eventName", "bookingDate", "reason", "riskScore", "status"}
    for entry in fraud_orders:
        missing = expected_fraud_fields - entry.keys()
        assert not missing, f"Fraud entry missing fields: {missing}"
        assert isinstance(entry["riskScore"], (int, float))
        assert isinstance(entry["reason"], str)
        assert isinstance(entry["bookingDate"], str)
        assert entry["eventName"] == EVENT["name"]

    if order["fraud_status"] == "fraud_review":
        assert any(e["id"] == order["id"] for e in fraud_orders), \
            "Flagged order should appear in fraud endpoint"

    # ── 8. Verify data isolation (separate organizer) ──
    org2_headers = {"Authorization": f"Bearer {register_and_login(client, 'org2_fraud_test@test.com', 'Org2 Fraud', 'pass123', 'organizer')}"}

    fraud_org2 = client.get("/organizer/fraud-orders", headers=org2_headers)
    assert fraud_org2.status_code == 200
    assert fraud_org2.json() == [], "Organizer should only see their own fraud orders"
    
    
def test_get_fraud_orders_returns_real_data(client, test_session):
    org_header =  {"Authorization": f'Bearer {register_and_login(client, 'orgfraud1@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custfraud1@test.com', 'Cust', 'pass123', 'customer')}'}
     
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 2}]
    }, headers=cust_header)
    assert order_response.status_code == 200
    order_id = order_response.json()['id']

    # Force this order into a flagged state, as if the model had flagged it
    order = test_session.get(Order, order_id)
    order.fraud_status = "fraud_review"
    order.fraud_reason = "Fraud probability 80.00% exceeds threshold"
    order.fraud_score = 0.80
    test_session.add(order)
    test_session.commit()

    response = client.get('/organizer/fraud-orders', headers=org_header)
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    entry = next(e for e in data if e["id"] == order_id)
    assert entry["reason"] == "Fraud probability 80.00% exceeds threshold"
    assert entry["riskScore"] == 80
    assert entry["status"] == "fraud_review"


def test_get_fraud_orders_only_shows_own_events(client, test_session):
    org1_header = {"Authorization": f'Bearer {register_and_login(client, 'orgfraud2@test.com', 'Org1', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org1_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custfraud2@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    order = test_session.get(Order, order_id)
    order.fraud_status = "fraud_review"
    order.fraud_reason = "Test reason"
    order.fraud_score = 0.9
    test_session.add(order)
    test_session.commit()

    org2_header = {"Authorization": f'Bearer {register_and_login(client, 'orgfraud3@test.com', 'Org2', 'pass123', 'organizer')}'}
    
    response = client.get('/organizer/fraud-orders', headers=org2_header)
    assert response.status_code == 200
    assert response.json() == []
    
# Action Routes:
def test_fraud_order_status_actions(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgfraud4@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header =  {"Authorization": f'Bearer {register_and_login(client, 'custfraud4@test.com', 'Cust', 'pass123', 'customer')}'}
   
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    order = test_session.get(Order, order_id)
    order.fraud_status = "fraud_review"
    test_session.add(order)
    test_session.commit()

    # Mark under review
    response = client.post(f'/organizer/fraud-orders/{order_id}/review', headers=org_header)
    assert response.status_code == 200
    test_session.refresh(order)
    assert order.fraud_status == "under_review"

    # Confirm fraud
    response = client.post(f'/organizer/fraud-orders/{order_id}/confirm', headers=org_header)
    assert response.status_code == 200
    test_session.refresh(order)
    assert order.fraud_status == "confirmed_fraud"

    # Dismiss
    response = client.post(f'/organizer/fraud-orders/{order_id}/dismiss', headers=org_header)
    assert response.status_code == 200
    test_session.refresh(order)
    assert order.fraud_status == "dismissed"


def test_fraud_order_action_forbidden_for_wrong_organizer(client, test_session):
    org1_header = {"Authorization": f'Bearer {register_and_login(client, 'orgfraud5@test.com', 'Org1', 'pass123', 'organizer')}'}
     
    event_data = setup_event_with_tiers(client, org1_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custfraud5@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    org2_header = {"Authorization": f'Bearer {register_and_login(client, 'orgfraud6@test.com', 'Org2', 'pass123', 'organizer')}'}
    response = client.post(f'/organizer/fraud-orders/{order_id}/confirm', headers=org2_header)
    assert response.status_code == 403



# Testing QR CODE generation :
from models.Ticket_entity import Ticket as TicketInstance
from models.Orders import Order, OrderItem


def create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=2):
    """Helper: creates an order, marks it paid, and lets the webhook-equivalent
    logic generate tickets — mirrors what handle_stripe_webhook does."""
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': quantity}]
    }, headers=cust_header)
    assert order_response.status_code == 200
    order_id = order_response.json()['id']

    order = test_session.get(Order, order_id)
    order.payment_status = "paid"
    test_session.add(order)

    items = test_session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    for item in items:
        for _ in range(item.quantity):
            ticket = TicketInstance(order_item_id=item.id)
            test_session.add(ticket)

    test_session.commit()
    return order_id


# ---------- GET /orders/{order_id}/tickets ----------

def test_get_order_tickets_success(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr1@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr1@test.com', 'Cust', 'pass123', 'customer')}'}
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=3)

    response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    assert response.status_code == 200
    tickets = response.json()

    assert len(tickets) == 3
    for t in tickets:
        assert "ticket_uid" in t
        assert t["status"] == "valid"
        assert t["category_name"] == event_data['ticket_tiers'][0]['category_name']

    # All ticket_uids should be unique
    uids = [t["ticket_uid"] for t in tickets]
    assert len(uids) == len(set(uids))


def test_get_order_tickets_wrong_user_forbidden(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr2@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr2@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    other_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr3@test.com', 'Cust2', 'pass123', 'customer')}'}
    response = client.get(f'/orders/{order_id}/tickets', headers=other_header)
    assert response.status_code == 403


def test_get_order_tickets_not_found(client):
    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr4@test.com', 'Cust', 'pass123', 'customer')}'}
    response = client.get('/orders/999999/tickets', headers=cust_header)
    assert response.status_code == 404


def test_get_order_tickets_empty_before_payment(client):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr5@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr5@test.com', 'Cust', 'pass123', 'customer')}'}
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    # No payment, no webhook triggered — tickets should not exist yet
    response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    assert response.status_code == 200
    assert response.json() == []


# ---------- GET /tickets/{ticket_uid}/qr ----------

def test_get_ticket_qr_returns_image(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr6@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr6@test.com', 'Cust', 'pass123', 'customer')}'}
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    response = client.get(f'/tickets/{ticket_uid}/qr', headers=cust_header)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0  # actual image bytes were returned


def test_get_ticket_qr_wrong_user_forbidden(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr7@test.com', 'Org', 'pass123', 'organizer')}'}
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr7@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    other_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr8@test.com', 'Cust2', 'pass123', 'customer')}'}
    response = client.get(f'/tickets/{ticket_uid}/qr', headers=other_header)
    assert response.status_code == 403


def test_get_ticket_qr_not_found(client):
    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr9@test.com', 'Cust', 'pass123', 'customer')}'}
    
    response = client.get('/tickets/nonexistent-uid-1234/qr', headers=cust_header)
    assert response.status_code == 404


# ---------- POST /checkin/{ticket_uid} ----------

def test_checkin_success(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr10@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr10@test.com', 'Cust', 'pass123', 'customer')}'}
    
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    response = client.post(f'/checkin/{ticket_uid}', headers=org_header)
    assert response.status_code == 200
    assert response.json()['ticket_uid'] == ticket_uid

    ticket = test_session.exec(
        select(TicketInstance).where(TicketInstance.ticket_uid == ticket_uid)
    ).first()
    assert ticket.status == "used"
    assert ticket.checked_in_at is not None


def test_checkin_already_used_rejected(client, test_session):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr11@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = {"Authorization": f'Bearer {register_and_login(client, 'custqr11@test.com', 'Cust', 'pass123', 'customer')}'}
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    first = client.post(f'/checkin/{ticket_uid}', headers=org_header)
    assert first.status_code == 200

    second = client.post(f'/checkin/{ticket_uid}', headers=org_header)
    assert second.status_code == 409


def test_checkin_invalid_uid(client):
    org_header = {"Authorization": f'Bearer {register_and_login(client, 'orgqr12@test.com', 'Org', 'pass123', 'organizer')}'}
    
    totally_fake_uid = 122212121212
    response = client.post(f'/checkin/{totally_fake_uid}', headers=org_header)
    assert response.status_code == 404


def test_checkin_forbidden_for_customer(client, test_session):
    org_header = {"Authorization": f'Bearer { register_and_login(client, 'orgqr13@test.com', 'Org', 'pass123', 'organizer')}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr13@test.com', 'Cust', 'pass123', 'customer')
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    # A customer (not organizer/staff) tries to check someone in
    response = client.post(f'/checkin/{ticket_uid}', headers=cust_header)
    assert response.status_code == 403
    
    
import io   
    
def make_fake_image(filename="banner.jpg", content_type="image/jpeg", size_bytes=1024):
    file_bytes = io.BytesIO(b"fake image content" * (size_bytes // 20 + 1))
    file_bytes.seek(0)
    return (filename, file_bytes, content_type)


def test_upload_event_banner_success(client, mock_supabase_upload):
    org_header = {"Authorization": f'Bearer { register_and_login(client, "banner_org@test.com", "Org", "pass123", "organizer")}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data["event"]["id"]

    filename, file_bytes, content_type = make_fake_image()
    response = client.post(
        f"/events/{event_id}/banner",
        files={"file": (filename, file_bytes, content_type)},
        headers=org_header,
    )

    assert response.status_code == 200
    data = response.json()
    assert "banner_url" in data
    assert data["banner_url"].startswith("https://")


def test_upload_event_banner_wrong_type_rejected(client, mock_supabase_upload):
    org_header = {"Authorization": f'Bearer { register_and_login(client, "banner_org2@test.com", "Org", "pass123", "organizer")}'}
   
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data["event"]["id"]

    filename, file_bytes, content_type = make_fake_image(
        filename="malware.exe", content_type="application/x-msdownload"
    )
    response = client.post(
        f"/events/{event_id}/banner",
        files={"file": (filename, file_bytes, content_type)},
        headers=org_header,
    )

    assert response.status_code == 400


def test_upload_event_banner_too_large_rejected(client, mock_supabase_upload):
    org_header = {"Authorization": f'Bearer { register_and_login(client, "banner_org3@test.com", "Org", "pass123", "organizer")}'}
     
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data["event"]["id"]

    # 6MB file — over your 5MB limit
    filename, file_bytes, content_type = make_fake_image(size_bytes=6 * 1024 * 1024)
    response = client.post(
        f"/events/{event_id}/banner",
        files={"file": (filename, file_bytes, content_type)},
        headers=org_header,
    )

    assert response.status_code == 400


def test_upload_event_banner_not_owner_rejected(client, mock_supabase_upload):
    org_header = {"Authorization": f'Bearer { register_and_login(client, "banner_org4@test.com", "Org", "pass123", "organizer")}'}
    
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data["event"]["id"]

    # A different organizer, not the one who created the event
    other_org_header = {"Authorization": f'Bearer { register_and_login(client, "banner_intruder@test.com", "Intruder", "pass123", "organizer")}'}
    filename, file_bytes, content_type = make_fake_image()
    response = client.post(
        f"/events/{event_id}/banner",
        files={"file": (filename, file_bytes, content_type)},
        headers=other_org_header,
    )

    assert response.status_code == 403


def test_upload_event_banner_event_not_found(client, mock_supabase_upload):
    org_header = register_and_login(client, "banner_org5@test.com", "Org", "pass123", "organizer")

    filename, file_bytes, content_type = make_fake_image()
    response = client.post(
        "/events/999999/banner",
        files={"file": (filename, file_bytes, content_type)},
        headers=org_header,
    )

    assert response.status_code == 404
    
    
    
# checking the Profile picture 
def test_upload_profile_picture_success(client, mock_supabase_upload):
    header = register_and_login(client, "pic_user@test.com", "PicUser", "pass123", "customer")

    filename, file_bytes, content_type = make_fake_image()
    response = client.post(
        "/users/me/profile-picture",
        files={"file": (filename, file_bytes, content_type)},
        headers=header,
    )

    assert response.status_code == 200
    data = response.json()
    assert "profile_picture_url" in data
    assert data["profile_picture_url"].startswith("https://")


def test_upload_profile_picture_wrong_type_rejected(client, mock_supabase_upload):
    header = register_and_login(client, "pic_user2@test.com", "PicUser", "pass123", "customer")

    filename, file_bytes, content_type = make_fake_image(
        filename="doc.pdf", content_type="application/pdf"
    )
    response = client.post(
        "/users/me/profile-picture",
        files={"file": (filename, file_bytes, content_type)},
        headers=header,
    )

    assert response.status_code == 400
    
    
# Checking the updated profile:
def test_update_user_profile_partial_update(client):
    header = register_and_login(client, "update_user@test.com", "OldName", "pass123", "customer")

    response = client.patch(
        "/users/me/update",
        json={"full_name": "New Name", "phone": "+1 555 0000"},
        headers=header,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "New Name"
    assert data["phone"] == "+1 555 0000"


def test_update_user_profile_does_not_wipe_unset_fields(client):
    header = register_and_login(client, "update_user2@test.com", "OldName", "pass123", "customer")

    # First update: set city
    client.patch("/users/me/update", json={"city": "Lahore"}, headers=header)

    # Second update: only send full_name, city should remain untouched
    response = client.patch(
        "/users/me/update",
        json={"full_name": "Updated Name"},
        headers=header,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["city"] == "Lahore"  # should NOT have been wiped
    
    
    
# Testing for change Password test : 
def test_change_password_success(client):
    header = register_and_login(client, "pwd_user@test.com", "PwdUser", "oldpass123", "customer")

    response = client.post(
        "/users/me/change-password",
        json={"current_password": "oldpass123", "new_password": "newpass456"},
        headers=header,
    )

    assert response.status_code == 200

    # confirm the new password actually works for login
    login_response = client.post("/auth/login", json={
        "email": "pwd_user@test.com", "password": "newpass456"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_change_password_wrong_old_password_rejected(client):
    header = register_and_login(client, "pwd_user2@test.com", "PwdUser", "correctpass", "customer")

    response = client.post(
        "/users/me/change-password",
        json={"current_password": "wrongpass", "new_password": "newpass456"},
        headers=header,
    )

    assert response.status_code == 401  # depends on what your service raises
    
    
# checking the booking history :

def test_booking_history_returns_orders(client):
    org_header = register_and_login(client, "booking_org@test.com", "Org", "pass123", "organizer")
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data["event"]["id"]
    event_name = event_data["event"]["name"]
    tier_id = event_data["ticket_tiers"][0]["id"]

    cust_header = register_and_login(client, "booking_cust@test.com", "Cust", "pass123", "customer")

    order_response = client.post("/orders", json={
        "event_id": event_id,
        "items": [{"ticket_tier_id": tier_id, "quantity": 1}]
    }, headers=cust_header)
    assert order_response.status_code == 200

    response = client.get("/users/me/booking-history", headers=cust_header)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    entry = data[0]
    assert "order_id" in entry
    assert entry["event_name"] == event_name
    assert "total_price" in entry
    assert "status" in entry


def test_booking_history_empty_for_new_user(client):
    header = register_and_login(client, "no_bookings@test.com", "NoBooking", "pass123", "customer")

    response = client.get("/users/me/booking-history", headers=header)

    assert response.status_code == 200
    assert response.json() == []
    
    
# Testing the Notification:

# tests/test_notifications.py
from models.Notification import Notification


def create_notification_for_user(session, user_id, title="Test notification", body="Test body", is_read=False):
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        is_read=is_read,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def get_user_id_from_token(client, header):
    """Helper: hit an authenticated route that returns user info to get the current user's id."""
    response = client.get("/users/me", headers=header)  # adjust if your 'me' route differs
    return response.json()["id"]


# ---------- GET /notifications ----------

def test_get_notifications_returns_users_notifications(client, test_session):
    header = register_and_login(client, "notif_user1@test.com", "NotifUser", "pass123", "customer")
    user_id = get_user_id_from_token(client, header)

    create_notification_for_user(test_session, user_id, title="Payment successful", body="Your payment was confirmed.")
    create_notification_for_user(test_session, user_id, title="Event reminder", body="Your event starts tomorrow.")

    response = client.get("/notifications", headers=header)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_notifications_empty_for_new_user(client):
    header = register_and_login(client, "notif_user2@test.com", "NotifUser", "pass123", "customer")

    response = client.get("/notifications", headers=header)

    assert response.status_code == 200
    assert response.json() == []


def test_get_notifications_only_returns_own_notifications(client, test_session):
    header1 = register_and_login(client, "notif_user3@test.com", "User1", "pass123", "customer")
    header2 = register_and_login(client, "notif_user4@test.com", "User2", "pass123", "customer")

    user1_id = get_user_id_from_token(client, header1)
    user2_id = get_user_id_from_token(client, header2)

    create_notification_for_user(test_session, user1_id, title="For user 1")
    create_notification_for_user(test_session, user2_id, title="For user 2")

    response = client.get("/notifications", headers=header1)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "For user 1"


def test_get_notifications_ordered_newest_first(client, test_session):
    header = register_and_login(client, "notif_user5@test.com", "NotifUser", "pass123", "customer")
    user_id = get_user_id_from_token(client, header)

    create_notification_for_user(test_session, user_id, title="Older")
    create_notification_for_user(test_session, user_id, title="Newer")

    response = client.get("/notifications", headers=header)

    data = response.json()
    assert data[0]["title"] == "Newer"
    assert data[1]["title"] == "Older"


# ---------- POST /notifications/{id}/read ----------

def test_mark_notification_read_success(client, test_session):
    header = register_and_login(client, "notif_user6@test.com", "NotifUser", "pass123", "customer")
    user_id = get_user_id_from_token(client, header)

    notification = create_notification_for_user(test_session, user_id, is_read=False)

    response = client.post(f"/notifications/{notification.id}/read", headers=header)

    assert response.status_code == 200
    assert response.json()["is_read"] is True


def test_mark_notification_read_persists(client, test_session):
    header = register_and_login(client, "notif_user7@test.com", "NotifUser", "pass123", "customer")
    user_id = get_user_id_from_token(client, header)

    notification = create_notification_for_user(test_session, user_id, is_read=False)

    mark_response = client.post(f"/notifications/{notification.id}/read", headers=header)
    assert mark_response.status_code == 200

    list_response = client.get("/notifications", headers=header)
    updated = next(n for n in list_response.json() if n["id"] == notification.id)
    assert updated["is_read"] is True


def test_mark_notification_read_not_found(client):
    header = register_and_login(client, "notif_user8@test.com", "NotifUser", "pass123", "customer")

    response = client.post("/notifications/999999/read", headers=header)

    assert response.status_code == 404


def test_mark_notification_read_wrong_owner_rejected(client, test_session):
    header1 = register_and_login(client, "notif_user9@test.com", "User1", "pass123", "customer")
    header2 = register_and_login(client, "notif_user10@test.com", "User2", "pass123", "customer")

    user1_id = get_user_id_from_token(client, header1)
    notification = create_notification_for_user(test_session, user1_id)

    response = client.post(f"/notifications/{notification.id}/read", headers=header2)

    assert response.status_code == 404


# ---------- DELETE /notifications/delete ----------

def test_delete_all_notifications_success(client, test_session):
    header = register_and_login(client, "notif_user11@test.com", "NotifUser", "pass123", "customer")
    user_id = get_user_id_from_token(client, header)

    create_notification_for_user(test_session, user_id, title="One")
    create_notification_for_user(test_session, user_id, title="Two")

    response = client.delete("/notifications/delete", headers=header)

    assert response.status_code == 200


def test_delete_all_notifications_persists(client, test_session):
    header = register_and_login(client, "notif_user12@test.com", "NotifUser", "pass123", "customer")
    user_id = get_user_id_from_token(client, header)

    create_notification_for_user(test_session, user_id)

    client.delete("/notifications/delete", headers=header)

    list_response = client.get("/notifications", headers=header)
    assert list_response.json() == []


def test_delete_all_notifications_does_not_affect_other_users(client, test_session):
    header1 = register_and_login(client, "notif_user13@test.com", "User1", "pass123", "customer")
    header2 = register_and_login(client, "notif_user14@test.com", "User2", "pass123", "customer")

    user1_id = get_user_id_from_token(client, header1)
    user2_id = get_user_id_from_token(client, header2)

    create_notification_for_user(test_session, user1_id)
    create_notification_for_user(test_session, user2_id)

    client.delete("/notifications/delete", headers=header1)

    user1_notifs = client.get("/notifications", headers=header1).json()
    user2_notifs = client.get("/notifications", headers=header2).json()

    assert user1_notifs == []
    assert len(user2_notifs) == 1
    
    
# Testing the Email sending OTP AUTH:


# tests/test_auth_verification.py

def get_last_sent_otp_code(mock_email_fixture):
    args, kwargs = mock_email_fixture.call_args
    return args[1] if len(args) > 1 else kwargs["code"]


def test_register_sends_verification_email(client, mock_email_sending):
    response = client.post("/auth/register", json={
        "email": "verify1@test.com",
        "full_name": "Verify User",
        "password": "pass123",
        "role": "customer",
    })

    assert response.status_code == 200
    mock_email_sending.assert_called_once()
    assert mock_email_sending.call_args[0][0] == "verify1@test.com"


def test_login_blocked_before_verification(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify2@test.com",
        "full_name": "Verify User2",
        "password": "pass123",
        "role": "customer",
    })

    response = client.post("/auth/login", json={
        "email": "verify2@test.com",
        "password": "pass123",
    })

    assert response.status_code == 403
    assert "verify" in response.json()["detail"].lower()


def test_verify_email_with_correct_code_succeeds(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify3@test.com",
        "full_name": "Verify User3",
        "password": "pass123",
        "role": "customer",
    })

    code = get_last_sent_otp_code(mock_email_sending)

    response = client.post("/auth/verify-email", json={
        "email": "verify3@test.com",
        "code": code,
    })

    assert response.status_code == 200


def test_verify_email_with_wrong_code_rejected(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify4@test.com",
        "full_name": "Verify User4",
        "password": "pass123",
        "role": "customer",
    })

    response = client.post("/auth/verify-email", json={
        "email": "verify4@test.com",
        "code": "000000",  # deliberately wrong
    })

    assert response.status_code == 400


def test_login_succeeds_after_verification(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify5@test.com",
        "full_name": "Verify User5",
        "password": "pass123",
        "role": "customer",
    })

    code = get_last_sent_otp_code(mock_email_sending)
    verify_response = client.post("/auth/verify-email", json={
        "email": "verify5@test.com",
        "code": code,
    })
    assert verify_response.status_code == 200

    login_response = client.post("/auth/login", json={
        "email": "verify5@test.com",
        "password": "pass123",
    })

    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_verify_email_code_cannot_be_reused(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify6@test.com",
        "full_name": "Verify User6",
        "password": "pass123",
        "role": "customer",
    })

    code = get_last_sent_otp_code(mock_email_sending)

    first_attempt = client.post("/auth/verify-email", json={"email": "verify6@test.com", "code": code})
    assert first_attempt.status_code == 200

    second_attempt = client.post("/auth/verify-email", json={"email": "verify6@test.com", "code": code})
    assert second_attempt.status_code == 400  # code already deleted from redis after first use


def test_resend_verification_sends_new_code(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify7@test.com",
        "full_name": "Verify User7",
        "password": "pass123",
        "role": "customer",
    })

    mock_email_sending.reset_mock()  # clear the call from registration

    response = client.post("/auth/resend-verification", json={"email": "verify7@test.com"})

    assert response.status_code == 200
    mock_email_sending.assert_called_once()


def test_resend_verification_unknown_email_rejected(client, mock_email_sending):
    response = client.post("/auth/resend-verification", json={"email": "doesnotexist@test.com"})
    assert response.status_code == 404


def test_resend_verification_already_verified_rejected(client, mock_email_sending):
    client.post("/auth/register", json={
        "email": "verify8@test.com",
        "full_name": "Verify User8",
        "password": "pass123",
        "role": "customer",
    })

    code = get_last_sent_otp_code(mock_email_sending)
    client.post("/auth/verify-email", json={"email": "verify8@test.com", "code": code})

    response = client.post("/auth/resend-verification", json={"email": "verify8@test.com"})
    assert response.status_code == 400
    
    
# tests/test_password_reset.py
import services.Password_reset_service as password_reset_module


def get_last_reset_code(mock_email_dict, email_expected=None):
    """Pulls the reset code from the mocked send_password_reset_email call."""
    mock_send = mock_email_dict["reset"]
    args, kwargs = mock_send.call_args
    return args[1] if len(args) > 1 else kwargs["code"]


# ---------- POST /auth/forgot-password ----------

def test_forgot_password_existing_email_sends_code(client, mock_email_sending):
    register_and_login(client, "resetuser1@test.com", "ResetUser", "oldpass123", "customer")
    mock_email_sending["reset"].reset_mock()  # clear any prior calls

    response = client.post("/auth/forgot-password", json={"email": "resetuser1@test.com"})

    assert response.status_code == 200
    mock_email_sending["reset"].assert_called_once()

    code = password_reset_module.redis_client.get("password_reset_code:resetuser1@test.com")
    assert code is not None


def test_forgot_password_nonexistent_email_returns_generic_response(client, mock_email_sending):
    """Should return the SAME response as a real email — no account-existence leak."""
    response = client.post("/auth/forgot-password", json={"email": "doesnotexist@test.com"})

    assert response.status_code == 200
    assert "if an account exists" in response.json()["detail"].lower()
    mock_email_sending["reset"].assert_not_called()


def test_forgot_password_response_identical_for_existing_and_nonexistent(client, mock_email_sending):
    """Confirms both code paths return the exact same message — this IS the security property."""
    register_and_login(client, "resetuser2@test.com", "ResetUser", "oldpass123", "customer")

    real_response = client.post("/auth/forgot-password", json={"email": "resetuser2@test.com"})
    fake_response = client.post("/auth/forgot-password", json={"email": "nosuchuser@test.com"})

    assert real_response.json() == fake_response.json()
    assert real_response.status_code == fake_response.status_code == 200


# ---------- POST /auth/verify-reset-code ----------

def test_verify_reset_code_success_returns_token(client, mock_email_sending):
    register_and_login(client, "resetuser3@test.com", "ResetUser", "oldpass123", "customer")
    client.post("/auth/forgot-password", json={"email": "resetuser3@test.com"})

    code = get_last_reset_code(mock_email_sending)

    response = client.post("/auth/verify-reset-code", json={
        "email": "resetuser3@test.com", "code": code
    })

    assert response.status_code == 200
    assert "reset_token" in response.json()


def test_verify_reset_code_wrong_code_rejected(client, mock_email_sending):
    register_and_login(client, "resetuser4@test.com", "ResetUser", "oldpass123", "customer")
    client.post("/auth/forgot-password", json={"email": "resetuser4@test.com"})

    response = client.post("/auth/verify-reset-code", json={
        "email": "resetuser4@test.com", "code": "000000"
    })

    assert response.status_code == 400


def test_verify_reset_code_expired_or_missing_rejected(client):
    """No forgot-password call was made, so no code exists in Redis."""
    register_and_login(client, "resetuser5@test.com", "ResetUser", "oldpass123", "customer")

    response = client.post("/auth/verify-reset-code", json={
        "email": "resetuser5@test.com", "code": "123456"
    })

    assert response.status_code == 400


def test_verify_reset_code_cannot_be_reused(client, mock_email_sending):
    register_and_login(client, "resetuser6@test.com", "ResetUser", "oldpass123", "customer")
    client.post("/auth/forgot-password", json={"email": "resetuser6@test.com"})
    code = get_last_reset_code(mock_email_sending)

    first = client.post("/auth/verify-reset-code", json={"email": "resetuser6@test.com", "code": code})
    assert first.status_code == 200

    second = client.post("/auth/verify-reset-code", json={"email": "resetuser6@test.com", "code": code})
    assert second.status_code == 400  # code was deleted from redis after first successful use


# ---------- POST /auth/reset-password ----------

def test_reset_password_success_and_login_works(client, mock_email_sending):
    register_and_login(client, "resetuser7@test.com", "ResetUser", "oldpass123", "customer")
    client.post("/auth/forgot-password", json={"email": "resetuser7@test.com"})
    code = get_last_reset_code(mock_email_sending)

    verify_response = client.post("/auth/verify-reset-code", json={
        "email": "resetuser7@test.com", "code": code
    })
    reset_token = verify_response.json()["reset_token"]

    reset_response = client.post("/auth/reset-password", json={
        "reset_token": reset_token, "new_password": "newpass456"
    })
    assert reset_response.status_code == 200

    # Confirm new password actually works for login
    login_response = client.post("/auth/login", json={
        "email": "resetuser7@test.com", "password": "newpass456"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Confirm OLD password no longer works
    old_login_response = client.post("/auth/login", json={
        "email": "resetuser7@test.com", "password": "oldpass123"
    })
    assert old_login_response.status_code == 401


def test_reset_password_invalid_token_rejected(client):
    response = client.post("/auth/reset-password", json={
        "reset_token": "totally-fake-token", "new_password": "newpass456"
    })

    assert response.status_code == 400


def test_reset_password_token_cannot_be_reused(client, mock_email_sending):
    register_and_login(client, "resetuser8@test.com", "ResetUser", "oldpass123", "customer")
    client.post("/auth/forgot-password", json={"email": "resetuser8@test.com"})
    code = get_last_reset_code(mock_email_sending)

    verify_response = client.post("/auth/verify-reset-code", json={
        "email": "resetuser8@test.com", "code": code
    })
    reset_token = verify_response.json()["reset_token"]

    first_reset = client.post("/auth/reset-password", json={
        "reset_token": reset_token, "new_password": "firstnewpass"
    })
    assert first_reset.status_code == 200

    second_reset = client.post("/auth/reset-password", json={
        "reset_token": reset_token, "new_password": "secondnewpass"
    })
    assert second_reset.status_code == 400  # token deleted after first use


# ---------- Full end-to-end flow ----------

def test_full_forgot_password_flow(client, mock_email_sending):
    register_and_login(client, "resetuser9@test.com", "ResetUser", "originalpass", "customer")

    forgot_response = client.post("/auth/forgot-password", json={"email": "resetuser9@test.com"})
    assert forgot_response.status_code == 200

    code = get_last_reset_code(mock_email_sending)

    verify_response = client.post("/auth/verify-reset-code", json={
        "email": "resetuser9@test.com", "code": code
    })
    assert verify_response.status_code == 200
    reset_token = verify_response.json()["reset_token"]

    reset_response = client.post("/auth/reset-password", json={
        "reset_token": reset_token, "new_password": "brandnewpass"
    })
    assert reset_response.status_code == 200

    login_response = client.post("/auth/login", json={
        "email": "resetuser9@test.com", "password": "brandnewpass"
    })
    assert login_response.status_code == 200