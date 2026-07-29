"""Fraud Detection Service.

Public API
----------
``predict_order(order, user, tier, session)``  →  ``FraudPrediction``

Usage from ``Order_services.py``::

    from services.fraud_detection import predict_order

    prediction = predict_order(order, user, tier, session)
    if prediction.is_fraud:
        order.status = fraud_config.flag_status

Architecture
------------
The rest of the application communicates with this module exclusively
through ``predict_order()``.  No other code should import from the
internal sub-modules (``config``, ``model_loader``, ``feature_builder``,
``predictor``, ``schemas``).

To replace the ML model:
  1. Train a new model and save as pickle/joblib.
  2. Update ``FRAUD_MODEL_PATH`` and ``FRAUD_PREPROCESSING_PATH``
     environment variables (or edit ``config.py``).
  3. If the new model expects different features, update
     ``feature_builder.py``.
  4. Restart the application.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from .config import fraud_config
from .predictor import predict
from .schemas import FraudPrediction, OrderContext

if TYPE_CHECKING:
    from sqlmodel import Session

    from models.Orders import Order
    from models.Ticket import TicketTier
    from models.Users import User

logger = logging.getLogger(__name__)


def _compute_user_stats(user_id: int, session: "Session") -> dict:
    """Compute aggregate spending stats and recent-activity features for a user.

    Returns a dict with all user-level features needed by the model.
    """
    from sqlmodel import select
    from models.Orders import Order as OrderModel

    stmt = select(OrderModel).where(
        OrderModel.user_id == user_id,
        OrderModel.status.in_(["pending", "paid"]),
    )
    all_orders = list(session.exec(stmt).all())

    total_orders = len(all_orders)
    total_spent = sum(o.total_price for o in all_orders)
    avg_value = total_spent / total_orders if total_orders > 0 else 0.0
    max_single = max((o.total_price for o in all_orders), default=0.0)

    # ── Refund / paid rates (all orders, not just pending/paid) ──
    all_stmt = select(OrderModel).where(OrderModel.user_id == user_id)
    all_user_orders = list(session.exec(all_stmt).all())
    refund_count = sum(1 for o in all_user_orders if o.status == "refunded")
    paid_count = sum(1 for o in all_user_orders if o.status == "paid")
    refund_rate = refund_count / len(all_user_orders) if all_user_orders else 0.0
    paid_rate = paid_count / len(all_user_orders) if all_user_orders else 1.0

    # ── Recent activity (last 1h / 24h / 7d) ──
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    seven_days_ago = now - timedelta(days=7)

    purchases_last_1h = 0
    purchases_last_24h = 0
    purchases_last_7d = 0
    spend_last_24h = 0.0
    spend_last_7d = 0.0
    distinct_events_24h: set = set()
    latest_order_time: datetime | None = None

    for o in all_user_orders:
        otime = o.created_at
        if otime is None:
            continue
        if otime.tzinfo is None:
            otime = otime.replace(tzinfo=timezone.utc)
        if otime >= one_hour_ago:
            purchases_last_1h += 1
        if otime >= one_day_ago:
            purchases_last_24h += 1
            spend_last_24h += o.total_price
            distinct_events_24h.add(o.event_id)
        if otime >= seven_days_ago:
            purchases_last_7d += 1
            spend_last_7d += o.total_price
        if latest_order_time is None or otime > latest_order_time:
            latest_order_time = otime

    time_since_last_order = 999999.0
    if latest_order_time is not None:
        diff = now - latest_order_time
        time_since_last_order = diff.total_seconds() / 3600.0

    return {
        "user_total_orders": total_orders,
        "user_total_spent": total_spent,
        "user_avg_order_value": avg_value,
        "user_max_single_order": max_single,
        "user_historical_refund_rate": refund_rate,
        "user_historical_paid_rate": paid_rate,
        "purchases_last_1h": purchases_last_1h,
        "purchases_last_24h": purchases_last_24h,
        "purchases_last_7d": purchases_last_7d,
        "spend_last_24h": spend_last_24h,
        "spend_last_7d": spend_last_7d,
        "distinct_events_last_24h": len(distinct_events_24h),
        "time_since_last_order_hours": time_since_last_order,
    }


def _compute_account_age_days(user: "User") -> int:
    """Compute the age of the user's account in days."""
    if not user.created_at:
        return 0
    now = datetime.now(timezone.utc)
    created = user.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    delta = now - created
    return max(delta.days, 0)


def _compute_organizer_refund_rate(organizer_id: int, session: "Session") -> float:
    """Compute the organizer's historical refund rate across all their events."""
    from sqlmodel import select
    from models.Event import Event as EventModel
    from models.Orders import Order as OrderModel

    event_ids = list(
        session.exec(
            select(EventModel.id).where(EventModel.organizer_id == organizer_id)
        ).all()
    )
    if not event_ids:
        return 0.0

    orders = list(
        session.exec(
            select(OrderModel).where(OrderModel.event_id.in_(event_ids))
        ).all()
    )
    if not orders:
        return 0.0

    refund_count = sum(1 for o in orders if o.status == "refunded")
    return refund_count / len(orders)


def predict_order(
    order: "Order",
    user: "User",
    tier: "TicketTier",
    session: "Session",
) -> FraudPrediction:
    """Evaluate an order for fraud risk.

    This is the **only** function the rest of the application should call.

    Args:
        order:   The newly created Order (not yet committed).
        user:    The user placing the order.
        tier:    The ticket tier being purchased.
        session: The database session (for user history queries).

    Returns:
        A ``FraudPrediction`` indicating whether the order is suspicious.
    """
    from models.Event import Event as EventModel

    event = session.get(EventModel, tier.event_id)

    user_stats = _compute_user_stats(user.id, session)
    account_age = _compute_account_age_days(user)
    org_refund_rate = _compute_organizer_refund_rate(
        event.organizer_id, session
    ) if event else 0.0

    ctx = OrderContext(
        # Order
        quantity=order.quantity,
        total_price=order.total_price,
        # Tier
        tier_price=tier.price,
        tier_currency=tier.currency,
        tier_total_seats=tier.total_seats,
        tier_sold_quantity=tier.sold_quantity,
        tier_category=tier.category_name,
        # Event
        event_id=tier.event_id,
        event_name=event.name if event else "",
        event_category=event.category if event else "",
        event_venue=event.venue if event else "",
        event_city=event.city if event else "",
        event_country=event.country if event else "",
        event_max_capacity=event.max_capacity if event else 0,
        event_start_datetime=event.start_datetime if event else None,
        event_created_at=event.created_at if event else None,
        # User
        user_id=user.id,
        user_email=user.email,
        user_full_name=user.full_name,
        user_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        user_is_verified=getattr(user, "is_verified", False),
        user_is_active=getattr(user, "is_active", True),
        user_account_age_days=account_age,
        is_first_order=user_stats["user_total_orders"] == 0,
        user_historical_refund_rate=user_stats["user_historical_refund_rate"],
        user_historical_paid_rate=user_stats["user_historical_paid_rate"],
        purchases_last_1h=user_stats["purchases_last_1h"],
        purchases_last_24h=user_stats["purchases_last_24h"],
        purchases_last_7d=user_stats["purchases_last_7d"],
        spend_last_24h=user_stats["spend_last_24h"],
        spend_last_7d=user_stats["spend_last_7d"],
        distinct_events_last_24h=user_stats["distinct_events_last_24h"],
        time_since_last_order_hours=user_stats["time_since_last_order_hours"],
        organizer_historical_refund_rate=org_refund_rate,
        # Legacy fields (kept for backward compatibility)
        user_total_orders=user_stats["user_total_orders"],
        user_total_spent=user_stats["user_total_spent"],
        user_avg_order_value=user_stats["user_avg_order_value"],
        user_max_single_order=user_stats["user_max_single_order"],
        # Timestamp
        order_created_at=order.created_at or datetime.now(timezone.utc),
    )

    logger.debug(
        "Building fraud context: user=%s event=%s tier=%s qty=%d total=%.2f",
        ctx.user_id,
        ctx.event_id,
        ctx.tier_category,
        ctx.quantity,
        ctx.total_price,
    )

    return predict(ctx)


__all__ = [
    "predict_order",
    "FraudPrediction",
    "OrderContext",
    "fraud_config",
]
