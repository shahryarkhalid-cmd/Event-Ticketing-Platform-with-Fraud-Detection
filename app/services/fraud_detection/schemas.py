"""Data structures for the fraud detection service.

Defines the input (OrderContext) and output (FraudPrediction) contracts
that decouple the fraud detection module from the rest of the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class OrderContext:
    """All information needed to evaluate an order for fraud.

    Populated from the existing User, TicketTier, and OrderCreate objects
    at the point of order creation. The fraud service never imports or
    depends on SQLAlchemy/SQLModel models directly — this dataclass is
    the sole interface.
    """

    # ── Order fields ──────────────────────────────────────────────
    quantity: int
    total_price: float

    # ── Ticket tier fields ────────────────────────────────────────
    tier_price: float
    tier_currency: str
    tier_total_seats: int
    tier_sold_quantity: int
    tier_category: str

    # ── Event fields ──────────────────────────────────────────────
    event_id: int
    event_name: str
    event_category: str
    event_venue: str
    event_city: str
    event_country: str
    event_max_capacity: int
    event_start_datetime: Optional[datetime] = None
    event_created_at: Optional[datetime] = None

    # ── User fields ───────────────────────────────────────────────
    user_id: int = 0
    user_email: str = ""
    user_full_name: str = ""
    user_role: str = ""
    user_is_verified: bool = False
    user_is_active: bool = True
    user_account_age_days: int = 0
    user_total_orders: int = 0
    user_total_spent: float = 0.0
    user_avg_order_value: float = 0.0
    user_max_single_order: float = 0.0

    # ── User behavioural features ─────────────────────────────────
    is_first_order: bool = True
    purchases_last_1h: int = 0
    purchases_last_24h: int = 0
    purchases_last_7d: int = 0
    spend_last_24h: float = 0.0
    spend_last_7d: float = 0.0
    distinct_events_last_24h: int = 0
    time_since_last_order_hours: float = 0.0
    user_historical_refund_rate: float = 0.0
    user_historical_paid_rate: float = 0.0
    organizer_historical_refund_rate: float = 0.0

    # ── Timestamp ─────────────────────────────────────────────────
    order_created_at: Optional[datetime] = None


@dataclass
class FraudPrediction:
    """Result of a fraud evaluation.

    The rest of the application only sees this object — it never
    interacts with the ML model directly.
    """

    is_fraud: bool
    fraud_probability: float
    model_name: str = "none"
    reason: str = ""
    model_version: Optional[str] = None

    def __str__(self) -> str:
        flag = "FRAUD" if self.is_fraud else "CLEAN"
        return (
            f"FraudPrediction({flag}, "
            f"prob={self.fraud_probability:.4f}, "
            f"model={self.model_name})"
        )
