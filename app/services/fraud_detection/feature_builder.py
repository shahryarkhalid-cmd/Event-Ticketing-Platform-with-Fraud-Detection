"""Transform an OrderContext into a model-ready feature matrix.

This module contains the feature-engineering logic that bridges the
application's domain objects and the ML model's expected input.

The ``app_schema`` mode is the production mode: it builds the 29 core
features that the trained sklearn Pipeline (loaded as ``best_model.pkl``)
expects.  The pipeline itself handles schema alignment, optional-column
defaults, cleaning, encoding, and scaling — so this builder only needs
to produce the raw core features with correct names.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

# Optional ML dependencies — fail-open if not installed
try:
    import pandas as pd

    _ML_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore[assignment]
    _ML_AVAILABLE = False

from .schemas import OrderContext

logger = logging.getLogger(__name__)


def require_ml_deps() -> None:
    """Raise ImportError with a clear message if ML deps are missing."""
    if not _ML_AVAILABLE:
        raise ImportError(
            "pandas is required for fraud detection. "
            "Install it with: pip install pandas"
        )


# ── Core feature builder (production mode) ────────────────────────


def _build_app_schema_features(ctx: OrderContext) -> Dict[str, Any]:
    """Extract the 29 core features from an OrderContext.

    Feature names and ordering match ``feature_list.json`` core_features
    exactly.  The sklearn Pipeline inside ``best_model.pkl`` handles
    optional-column defaults, imputation, encoding, and scaling.
    """
    now = ctx.order_created_at or datetime.now(timezone.utc)

    # ── Temporal features derived from order timestamp ──
    purchase_hour = float(now.hour)
    purchase_weekday = float(now.weekday())
    purchase_month = float(now.month)
    is_weekend = 1.0 if purchase_weekday >= 5.0 else 0.0
    is_late_night = 1.0 if purchase_hour < 6.0 else 0.0

    # ── Days until event starts ──
    days_until_event = 0.0
    if ctx.event_start_datetime:
        event_dt = ctx.event_start_datetime
        if event_dt.tzinfo is None and now.tzinfo is not None:
            now_for_delta = now.replace(tzinfo=None)
        elif event_dt.tzinfo is not None and now.tzinfo is None:
            now_for_delta = now
        else:
            now_for_delta = now
        delta = event_dt - now_for_delta
        days_until_event = float(delta.days)

    # ── Hours since tier was listed (use event.created_at as proxy) ──
    hours_since_tier_listed = 0.0
    if ctx.event_created_at:
        created = ctx.event_created_at
        if created.tzinfo is None and now.tzinfo is not None:
            created = created.replace(tzinfo=timezone.utc)
        elif created.tzinfo is not None and now.tzinfo is None:
            now_for_calc = now
        else:
            now_for_calc = now
        delta = now_for_calc - created
        hours_since_tier_listed = delta.total_seconds() / 3600.0

    # ── Price features ──
    price_per_ticket = ctx.total_price / ctx.quantity if ctx.quantity > 0 else ctx.tier_price
    price_deviation_from_listed = price_per_ticket - ctx.tier_price

    return {
        "quantity": float(ctx.quantity),
        "total_price": ctx.total_price,
        "price_per_ticket": price_per_ticket,
        "price_deviation_from_listed": price_deviation_from_listed,
        "account_age_days": float(ctx.user_account_age_days),
        "purchases_last_1h": float(ctx.purchases_last_1h),
        "purchases_last_24h": float(ctx.purchases_last_24h),
        "purchases_last_7d": float(ctx.purchases_last_7d),
        "spend_last_24h": ctx.spend_last_24h,
        "spend_last_7d": ctx.spend_last_7d,
        "distinct_events_last_24h": float(ctx.distinct_events_last_24h),
        "time_since_last_order_hours": ctx.time_since_last_order_hours,
        "user_lifetime_order_count": float(ctx.user_total_orders),
        "user_historical_refund_rate": ctx.user_historical_refund_rate,
        "user_historical_paid_rate": ctx.user_historical_paid_rate,
        "purchase_hour": purchase_hour,
        "purchase_weekday": purchase_weekday,
        "purchase_month": purchase_month,
        "days_until_event": days_until_event,
        "hours_since_tier_listed": hours_since_tier_listed,
        "quantity_share_of_tier_capacity": (
            float(ctx.quantity) / float(ctx.tier_total_seats)
            if ctx.tier_total_seats > 0 else 0.0
        ),
        "event_popularity_ratio": (
            float(ctx.tier_sold_quantity) / float(ctx.event_max_capacity)
            if ctx.event_max_capacity > 0 else 0.0
        ),
        "organizer_historical_refund_rate": ctx.organizer_historical_refund_rate,
        "is_verified": float(ctx.user_is_verified),
        "is_active": float(ctx.user_is_active),
        "is_first_order": float(ctx.is_first_order),
        "is_weekend": is_weekend,
        "is_late_night": is_late_night,
        "event_category": ctx.event_category,
    }


# ── Public API ────────────────────────────────────────────────────


def build_features(
    ctx: OrderContext,
    preprocessing: Any = None,
):
    """Build a model-ready feature DataFrame from an OrderContext.

    Args:
        ctx:           The order context to extract features from.
        preprocessing: The preprocessing artifacts (unused in app_schema
                       mode — the full Pipeline in best_model.pkl handles
                       schema alignment, cleaning, encoding, and scaling).

    Returns:
        A single-row ``pd.DataFrame`` with core features whose column
        names match ``feature_list.json`` core_features exactly.

    Raises:
        ImportError: If pandas is not installed.
    """
    require_ml_deps()

    raw = _build_app_schema_features(ctx)
    df = pd.DataFrame([raw])
    logger.debug(
        "Core feature matrix built: columns=%s",
        list(df.columns),
    )
    return df
