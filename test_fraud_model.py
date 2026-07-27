import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "app"))

from sqlmodel import Session, select
from database import engine
from models.Users import User
from models.Ticket import TicketTier
from models.Orders import Order
from services.fraud_detection import predict_order


with Session(engine) as session:
    user = session.exec(
        select(User).where(User.role == "customer")
    ).first()

    if not user:
        print("No customer found.")
        exit()

    tier = session.exec(select(TicketTier)).first()

    if not tier:
        print("No ticket tier found.")
        exit()

    order = Order(
        user_id=user.id,
        event_id=tier.event_id,
        ticket_tier_id=tier.id,
        quantity=2,
        total_price=tier.price * 2,
        status="pending",
    )

    print("=" * 60)
    print("Testing fraud prediction...")
    print("=" * 60)

    prediction = predict_order(order, user, tier, session)

    print("\nPrediction completed successfully.\n")

    print(f"Fraud          : {prediction.is_fraud}")
    print(f"Probability    : {prediction.fraud_probability:.4f}")
    print(f"Reason         : {prediction.reason}")
    print(f"Model          : {prediction.model_name}")
