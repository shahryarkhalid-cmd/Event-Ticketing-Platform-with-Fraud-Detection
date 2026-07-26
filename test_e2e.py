"""
End-to-end test: verify model_loader → feature_builder → predictor
works with a synthetic OrderContext.
"""
import sys
sys.path.insert(0, "app")

from datetime import datetime, timezone, timedelta
from app.services.fraud_detection.model_loader import load_artifacts, reset
from app.services.fraud_detection.feature_builder import build_features
from app.services.fraud_detection.schemas import OrderContext

# Force fresh load
reset()

# 1. Load model
print("Loading model artifacts...")
model, preprocessing = load_artifacts()
print(f"  Model type: {type(model).__name__}")
print(f"  Preprocessing type: {type(preprocessing).__name__}")

# 2. Build a synthetic OrderContext (low-risk order)
now = datetime.now(timezone.utc)
ctx_clean = OrderContext(
    quantity=2,
    total_price=50.00,
    tier_price=25.00,
    tier_currency="USD",
    tier_total_seats=500,
    tier_sold_quantity=100,
    tier_category="General",
    event_id=1,
    event_name="Jazz Night",
    event_category="Music",
    event_venue="Blue Note",
    event_city="New York",
    event_country="US",
    event_max_capacity=1000,
    event_start_datetime=now + timedelta(days=14),
    event_created_at=now - timedelta(days=30),
    user_id=9999,
    user_email="test@example.com",
    user_full_name="Test User",
    user_role="customer",
    user_is_verified=True,
    user_is_active=True,
    user_account_age_days=365,
    user_total_orders=10,
    user_total_spent=500.00,
    user_avg_order_value=50.00,
    user_max_single_order=100.00,
    is_first_order=False,
    purchases_last_1h=0,
    purchases_last_24h=1,
    purchases_last_7d=2,
    spend_last_24h=25.00,
    spend_last_7d=50.00,
    distinct_events_last_24h=1,
    time_since_last_order_hours=48.0,
    user_historical_refund_rate=0.0,
    user_historical_paid_rate=1.0,
    organizer_historical_refund_rate=0.02,
    order_created_at=now,
)

print("\nBuilding features for LOW-risk order...")
features = build_features(ctx_clean, preprocessing)
print(f"  Features shape: {features.shape}")
print(f"  Columns: {list(features.columns)}")

print("\nRunning prediction...")
label = model.predict(features)[0]
proba = model.predict_proba(features)[0, 1]
print(f"  Label: {label}")
print(f"  Fraud probability: {proba:.4f}")
print(f"  Is fraud: {label == 1 or proba >= 0.5}")

# 3. Build a high-risk OrderContext
ctx_risky = OrderContext(
    quantity=20,
    total_price=2000.00,
    tier_price=25.00,
    tier_currency="USD",
    tier_total_seats=500,
    tier_sold_quantity=490,
    tier_category="VIP",
    event_id=2,
    event_name="Sold Out Concert",
    event_category="Music",
    event_venue="Arena",
    event_city="Unknown",
    event_country="XX",
    event_max_capacity=500,
    event_start_datetime=now + timedelta(hours=2),
    event_created_at=now - timedelta(hours=1),
    user_id=8888,
    user_email="suspicious@tempmail.com",
    user_full_name="Suspicious User",
    user_role="customer",
    user_is_verified=False,
    user_is_active=True,
    user_account_age_days=1,
    user_total_orders=1,
    user_total_spent=2000.00,
    user_avg_order_value=2000.00,
    user_max_single_order=2000.00,
    is_first_order=True,
    purchases_last_1h=5,
    purchases_last_24h=5,
    purchases_last_7d=5,
    spend_last_24h=2000.00,
    spend_last_7d=2000.00,
    distinct_events_last_24h=5,
    time_since_last_order_hours=0.01,
    user_historical_refund_rate=0.0,
    user_historical_paid_rate=1.0,
    organizer_historical_refund_rate=0.20,
    order_created_at=now,
)

print("\nBuilding features for HIGH-risk order...")
features_risky = build_features(ctx_risky, preprocessing)
label_risky = model.predict(features_risky)[0]
proba_risky = model.predict_proba(features_risky)[0, 1]
print(f"  Label: {label_risky}")
print(f"  Fraud probability: {proba_risky:.4f}")
print(f"  Is fraud: {label_risky == 1 or proba_risky >= 0.5}")

print("\n[PASS] End-to-end test PASSED" if proba_risky > proba else "\n[FAIL] High-risk prob should be > low-risk prob")
print(f"  Low-risk: {proba:.4f}, High-risk: {proba_risky:.4f}")
