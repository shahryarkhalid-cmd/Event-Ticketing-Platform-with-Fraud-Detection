import pytest 
from conftest import client
from models.Users import User , UserRole
from sqlmodel import select
from models.Orders import CartItem
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
# Testing the dashboard graphs of the Organizer Window:
from models.Orders import Order
def test_get_analytics_summary(client , test_session):
    client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' , 'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
    org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
    assert org_client.status_code == 200
    header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
    
    create_response = client.post('/publish-event' , json=EVENT , headers = header)
    event_id = create_response.json()['event']['id']
    client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
    customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
    header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
    
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
            client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' , 'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
            org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
            assert org_client.status_code == 200
            header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
            
            create_response = client.post('/publish-event' , json=EVENT , headers = header)
            event_id = create_response.json()['event']['id']
            client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
            customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
            header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
            
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
        client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' ,       'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
        org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
        assert org_client.status_code == 200
        header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
        
        create_response = client.post('/publish-event' , json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
        customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
        header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
        
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
        client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' ,       'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
        org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
        assert org_client.status_code == 200
        header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
        
        create_response = client.post('/publish-event' , json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        customer_2 = client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
        customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
        header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
        
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
        assert vip_item['email'] == 'customer@gmail.com'
        assert vip_item['event'] == create_response.json()['event']['name']
        assert vip_item['qty'] == 10
        assert vip_item['qr_generated'] == False
        


# Testing revenue :

def test_revenue(client , test_session):
    
        client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' ,       'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
        org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
        assert org_client.status_code == 200
        header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
        
        create_response = client.post('/publish-event' , json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        customer_2 = client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
        customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
        header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
        
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
            client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' ,       'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
            org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
            assert org_client.status_code == 200
            header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
            
            create_response = client.post('/publish-event' , json=EVENT , headers = header)
            event_id = create_response.json()['event']['id']
            customer_2 = client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
            customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
            header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
            
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
            client.post('/auth/register' , json = {'email': 'organizer@test.gmail.com' ,       'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
            org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
            assert org_client.status_code == 200
            header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
            
            create_response = client.post('/publish-event' , json=EVENT , headers = header)
            event_id = create_response.json()['event']['id']
            customer_2 = client.post('/auth/register' , json={'email' : 'customer@gmail.com' , 'full_name' : 'customer' , 'password' : '123' , 'role' : 'customer'})
            customer = client.post('/auth/login' , json= {'email' : 'customer@gmail.com' , 'password':'123'})
            header_customer ={"Authorization": f'Bearer {customer.json()["access_token"]}'}
            
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
def test_update_event(client):
        client.post('/auth/register' , json = {'email':    'organizer@test.gmail.com' ,       'password' : 'test123' ,'full_name' : 'shahryar' , 'role' : 'organizer'})
        org_client = client.post('/auth/login' , json = {'email' : 'organizer@test.gmail.com' , 'password' : 'test123'})
        assert org_client.status_code == 200
        header={"Authorization": f'Bearer {org_client.json()['access_token']}'}
            
        create_response = client.post('/publish-event' ,json=EVENT , headers = header)
        event_id = create_response.json()['event']['id']
        response = client.put(f'/update_event/{event_id}', json =EVENT_2, headers = header)
        assert response.status_code == 200
        assert response.json()['event']['name'] == 'Tekken Event'
        
        
        
# Testing customer Routes :
from models.Orders import Order


def register_and_login(client, email, full_name, password, role):
    client.post('/auth/register', json={
        'email': email, 'full_name': full_name, 'password': password, 'role': role
    })
    login_ = client.post('/auth/login', json={'email': email, 'password': password})
    token = login_.json()['access_token']
    return {"Authorization": f'Bearer {token}'}


def setup_event_with_tiers(client, org_header):
    create_response = client.post('/publish-event', json=EVENT, headers=org_header)
    assert create_response.status_code == 200
    return create_response.json()


# ---------- POST /orders ----------

def test_create_order_success(client):
    org_header = register_and_login(client, 'org1@test.com', 'Org', 'pass123', 'organizer')
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
    org_header = register_and_login(client, 'org2@test.com', 'Org', 'pass123', 'organizer')
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
    org_header = register_and_login(client, 'org3@test.com', 'Org', 'pass123', 'organizer')
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
    org_header = register_and_login(client, 'org4@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust4@test.com', 'Cust', 'pass123', 'customer')

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
    cust_header = register_and_login(client, 'cust5@test.com', 'Cust', 'pass123', 'customer')
    response = client.get('/orders/me', headers=cust_header)
    assert response.status_code == 200
    assert response.json() == []


# ---------- GET /orders/{order_id} ----------

def test_get_order_status(client):
    org_header = register_and_login(client, 'org6@test.com', 'Org', 'pass123', 'organizer')
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
    org_header = register_and_login(client, 'org7@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust7@test.com', 'Cust', 'pass123', 'customer')
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
    cust_header = register_and_login(client, 'cust9@test.com', 'Cust', 'pass123', 'customer')
    response = client.get('/orders/999999', headers=cust_header)
    assert response.status_code == 404


# ---------- POST /orders/{order_id}/checkout ----------

def test_create_checkout_session(client):
    org_header = register_and_login(client, 'org10@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust10@test.com', 'Cust', 'pass123', 'customer')
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    response = client.post(f'/orders/{order_id}/checkout', headers=cust_header)
    assert response.status_code == 200
    assert "checkout_url" in response.json()


def test_checkout_wrong_user_forbidden(client):
    org_header = register_and_login(client, 'org11@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust11@test.com', 'Cust', 'pass123', 'customer')
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    other_header = register_and_login(client, 'cust12@test.com', 'Cust2', 'pass123', 'customer')
    response = client.post(f'/orders/{order_id}/checkout', headers=other_header)
    assert response.status_code == 409


def test_checkout_non_pending_order_rejected(client, test_session):
    org_header = register_and_login(client, 'org13@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'cust13@test.com', 'Cust', 'pass123', 'customer')
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
    org_header = register_and_login(client, 'orgwh@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custwh@test.com', 'Cust', 'pass123', 'customer')
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
    client.post('/auth/register', json={
        'email': 'org_fraud_test@test.com', 'full_name': 'Org Fraud', 'password': 'pass123', 'role': 'organizer'
    })
    org_login = client.post('/auth/login', json={
        'email': 'org_fraud_test@test.com', 'password': 'pass123'
    })
    org_headers = {"Authorization": f"Bearer {org_login.json()['access_token']}"}

    event_resp = client.post("/publish-event", json=EVENT, headers=org_headers)
    assert event_resp.status_code == 200
    tier_id = event_resp.json()['ticket_tiers'][0]['id']
    event_id = event_resp.json()['event']['id']

    # ── 2. Customer registration & role assignment ──
    client.post('/auth/register', json={
        'email': 'cust_fraud_test@test.com', 'full_name': 'Cust Fraud', 'password': 'pass123', 'role': 'customer'
    })
    customer = test_session.exec(select(User).where(User.email == 'cust_fraud_test@test.com')).first()
    customer.role = UserRole.customer
    test_session.add(customer)
    test_session.commit()

    cust_login = client.post('/auth/login', json={
        'email': 'cust_fraud_test@test.com', 'password': 'pass123'
    })
    cust_headers = {"Authorization": f"Bearer {cust_login.json()['access_token']}"}

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
    client.post('/auth/register', json={
        'email': 'org2_fraud_test@test.com', 'full_name': 'Org2 Fraud', 'password': 'pass123', 'role': 'organizer'
    })
    org2_login = client.post('/auth/login', json={
        'email': 'org2_fraud_test@test.com', 'password': 'pass123'
    })
    org2_headers = {"Authorization": f"Bearer {org2_login.json()['access_token']}"}

    fraud_org2 = client.get("/organizer/fraud-orders", headers=org2_headers)
    assert fraud_org2.status_code == 200
    assert fraud_org2.json() == [], "Organizer should only see their own fraud orders"
    
    
def test_get_fraud_orders_returns_real_data(client, test_session):
    org_header = register_and_login(client, 'orgfraud1@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custfraud1@test.com', 'Cust', 'pass123', 'customer')

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
    org1_header = register_and_login(client, 'orgfraud2@test.com', 'Org1', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org1_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custfraud2@test.com', 'Cust', 'pass123', 'customer')
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

    org2_header = register_and_login(client, 'orgfraud3@test.com', 'Org2', 'pass123', 'organizer')
    response = client.get('/organizer/fraud-orders', headers=org2_header)
    assert response.status_code == 200
    assert response.json() == []
    
# Action Routes:
def test_fraud_order_status_actions(client, test_session):
    org_header = register_and_login(client, 'orgfraud4@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custfraud4@test.com', 'Cust', 'pass123', 'customer')
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
    org1_header = register_and_login(client, 'orgfraud5@test.com', 'Org1', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org1_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custfraud5@test.com', 'Cust', 'pass123', 'customer')
    order_response = client.post('/orders', json={
        'event_id': event_id,
        'items': [{'ticket_tier_id': tier_id, 'quantity': 1}]
    }, headers=cust_header)
    order_id = order_response.json()['id']

    org2_header = register_and_login(client, 'orgfraud6@test.com', 'Org2', 'pass123', 'organizer')
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
    org_header = register_and_login(client, 'orgqr1@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr1@test.com', 'Cust', 'pass123', 'customer')
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
    org_header = register_and_login(client, 'orgqr2@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr2@test.com', 'Cust', 'pass123', 'customer')
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    other_header = register_and_login(client, 'custqr3@test.com', 'Cust2', 'pass123', 'customer')
    response = client.get(f'/orders/{order_id}/tickets', headers=other_header)
    assert response.status_code == 403


def test_get_order_tickets_not_found(client):
    cust_header = register_and_login(client, 'custqr4@test.com', 'Cust', 'pass123', 'customer')
    response = client.get('/orders/999999/tickets', headers=cust_header)
    assert response.status_code == 404


def test_get_order_tickets_empty_before_payment(client):
    org_header = register_and_login(client, 'orgqr5@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr5@test.com', 'Cust', 'pass123', 'customer')
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
    org_header = register_and_login(client, 'orgqr6@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr6@test.com', 'Cust', 'pass123', 'customer')
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    response = client.get(f'/tickets/{ticket_uid}/qr', headers=cust_header)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0  # actual image bytes were returned


def test_get_ticket_qr_wrong_user_forbidden(client, test_session):
    org_header = register_and_login(client, 'orgqr7@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr7@test.com', 'Cust', 'pass123', 'customer')
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    other_header = register_and_login(client, 'custqr8@test.com', 'Cust2', 'pass123', 'customer')
    response = client.get(f'/tickets/{ticket_uid}/qr', headers=other_header)
    assert response.status_code == 403


def test_get_ticket_qr_not_found(client):
    cust_header = register_and_login(client, 'custqr9@test.com', 'Cust', 'pass123', 'customer')
    response = client.get('/tickets/nonexistent-uid-1234/qr', headers=cust_header)
    assert response.status_code == 404


# ---------- POST /checkin/{ticket_uid} ----------

def test_checkin_success(client, test_session):
    org_header = register_and_login(client, 'orgqr10@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr10@test.com', 'Cust', 'pass123', 'customer')
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
    org_header = register_and_login(client, 'orgqr11@test.com', 'Org', 'pass123', 'organizer')
    event_data = setup_event_with_tiers(client, org_header)
    event_id = event_data['event']['id']
    tier_id = event_data['ticket_tiers'][0]['id']

    cust_header = register_and_login(client, 'custqr11@test.com', 'Cust', 'pass123', 'customer')
    order_id = create_paid_order_with_tickets(client, test_session, org_header, cust_header, event_id, tier_id, quantity=1)

    tickets_response = client.get(f'/orders/{order_id}/tickets', headers=cust_header)
    ticket_uid = tickets_response.json()[0]['ticket_uid']

    first = client.post(f'/checkin/{ticket_uid}', headers=org_header)
    assert first.status_code == 200

    second = client.post(f'/checkin/{ticket_uid}', headers=org_header)
    assert second.status_code == 409


def test_checkin_invalid_uid(client):
    org_header = register_and_login(client, 'orgqr12@test.com', 'Org', 'pass123', 'organizer')
    totally_fake_uid = 122212121212
    response = client.post(f'/checkin/{totally_fake_uid}', headers=org_header)
    assert response.status_code == 404


def test_checkin_forbidden_for_customer(client, test_session):
    org_header = register_and_login(client, 'orgqr13@test.com', 'Org', 'pass123', 'organizer')
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