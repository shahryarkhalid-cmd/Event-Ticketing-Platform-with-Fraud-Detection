"""
Schema contract: the single source of truth for which features are CORE
(always derivable from the application's existing DB models — User, Event,
TicketTier, Order — with zero app changes) versus OPTIONAL (require data the
application does not capture today: device, network, payment-attempt
telemetry, phone verification).

Design note on "the application's available fields": the live app's DB
models already carry more than a raw HTTP request body would — e.g.
`book_ticket()` has the full User/Event/TicketTier objects in hand, not just
the client's JSON payload. CORE features here are anything computable from
those existing models and the Order history table, with no new capture, no
migration, and no endpoint change. That is the intended reading of "only
fields the application already sends" for this project; OPTIONAL is
everything beyond that.

Nothing in OPTIONAL_FEATURES is ever required. Every optional column has a
documented default substituted by `align_to_schema()` when absent, so the
preprocessing pipeline and the model always succeed on core-only input.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# CORE features — always available from existing app models, no changes needed
# --------------------------------------------------------------------------- #
CORE_NUMERIC_FEATURES = [
    "quantity",
    "total_price",
    "price_per_ticket",
    "price_deviation_from_listed",
    "account_age_days",
    "purchases_last_1h",
    "purchases_last_24h",
    "purchases_last_7d",
    "spend_last_24h",
    "spend_last_7d",
    "distinct_events_last_24h",
    "time_since_last_order_hours",
    "user_lifetime_order_count",
    "user_historical_refund_rate",
    "user_historical_paid_rate",
    "purchase_hour",
    "purchase_weekday",
    "purchase_month",
    "days_until_event",
    "hours_since_tier_listed",
    "quantity_share_of_tier_capacity",
    "event_popularity_ratio",
    "organizer_historical_refund_rate",
]
CORE_BOOLEAN_FEATURES = [
    "is_verified",
    "is_active",
    "is_first_order",
    "is_weekend",
    "is_late_night",
]
CORE_CATEGORICAL_FEATURES = [
    "event_category",
]
CORE_FEATURES = CORE_NUMERIC_FEATURES + CORE_BOOLEAN_FEATURES + CORE_CATEGORICAL_FEATURES

# --------------------------------------------------------------------------- #
# OPTIONAL features — require capture the app does not do today.
# Every one has a safe default used by align_to_schema() when the column is
# missing entirely (not just null on some rows — genuinely absent).
# --------------------------------------------------------------------------- #
OPTIONAL_NUMERIC_DEFAULTS = {
    "failed_payments": 0.0,
    "payment_attempts": 0.0,
    "purchases_same_device_24h": 0.0,
    "purchases_same_ip_24h": 0.0,
    "purchases_same_card_24h": 0.0,
    "unique_devices_per_user": 0.0,
    "unique_cards_per_device": 0.0,
}
OPTIONAL_BOOLEAN_DEFAULTS = {
    "vpn_detected": 0.0,
    "proxy_detected": 0.0,
    "datacenter_ip": 0.0,
    "phone_verified": 0.0,
    "ip_event_country_mismatch": 0.0,
}
OPTIONAL_CATEGORICAL_DEFAULTS = {
    "device_type": "Unknown",
    "browser": "Unknown",
    "operating_system": "Unknown",
    "ip_country": "Unknown",
    "ip_city": "Unknown",
}
OPTIONAL_DEFAULTS = {**OPTIONAL_NUMERIC_DEFAULTS, **OPTIONAL_BOOLEAN_DEFAULTS, **OPTIONAL_CATEGORICAL_DEFAULTS}

OPTIONAL_NUMERIC_FEATURES = list(OPTIONAL_NUMERIC_DEFAULTS) + list(OPTIONAL_BOOLEAN_DEFAULTS)
OPTIONAL_CATEGORICAL_FEATURES = list(OPTIONAL_CATEGORICAL_DEFAULTS)
OPTIONAL_FEATURES = OPTIONAL_NUMERIC_FEATURES + OPTIONAL_CATEGORICAL_FEATURES

ALL_NUMERIC_FEATURES = CORE_NUMERIC_FEATURES + CORE_BOOLEAN_FEATURES + OPTIONAL_NUMERIC_FEATURES
ALL_CATEGORICAL_FEATURES = CORE_CATEGORICAL_FEATURES + OPTIONAL_CATEGORICAL_FEATURES
ALL_FEATURES = ALL_NUMERIC_FEATURES + ALL_CATEGORICAL_FEATURES

# --------------------------------------------------------------------------- #
# Columns that must NEVER be used as model input (see feature_engineering.py
# for the full leakage rationale for each).
# --------------------------------------------------------------------------- #
LEAKAGE_COLUMNS = [
    "status",           # the current order's own settlement outcome — not known at scoring time
    "has_qr_code",      # generated only after successful payment
    "fraud_type",       # synthetic debug/audit column, not a real feature
    "is_fraud",         # the label itself
]
IDENTIFIER_COLUMNS = [
    "order_id", "user_id", "event_id", "tier_id",
    "device_id", "ip_address", "card_fingerprint", "user_agent", "created_at",
]


def align_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure every OPTIONAL_FEATURES column exists, inserting the documented
    default when a column is missing entirely. CORE_FEATURES are never
    defaulted here — if a core column is missing, that's a real ingestion
    bug upstream, not something this function should silently paper over.

    Safe to call on a single-row inference DataFrame that only contains
    core fields: every optional column will be added back with its default,
    and the preprocessing pipeline downstream will behave identically to
    training-time rows that happened to have missing optional data.
    """
    df = df.copy()
    for col in df.columns:
        if isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = df[col].astype(object)

    missing_core = [c for c in CORE_FEATURES if c not in df.columns]
    if missing_core:
        raise ValueError(
            f"Missing required CORE feature(s): {missing_core}. These must always be "
            "computable from the application's existing data — this indicates an "
            "upstream feature-engineering bug, not a case for a default value."
        )
    for col, default in OPTIONAL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
        else:
            if isinstance(df[col].dtype, pd.CategoricalDtype):
                df[col] = df[col].astype(object)
            df[col] = df[col].fillna(default)
    return df[CORE_FEATURES + OPTIONAL_FEATURES]


@dataclass
class SchemaManifest:
    """Serializable record of the schema contract, saved alongside model artifacts."""
    core_features: list = field(default_factory=lambda: list(CORE_FEATURES))
    optional_features: list = field(default_factory=lambda: list(OPTIONAL_FEATURES))
    optional_defaults: dict = field(default_factory=lambda: dict(OPTIONAL_DEFAULTS))
    numeric_features: list = field(default_factory=lambda: list(ALL_NUMERIC_FEATURES))
    categorical_features: list = field(default_factory=lambda: list(ALL_CATEGORICAL_FEATURES))

    def to_dict(self) -> dict:
        return {
            "core_features": self.core_features,
            "optional_features": self.optional_features,
            "optional_defaults": self.optional_defaults,
            "numeric_features": self.numeric_features,
            "categorical_features": self.categorical_features,
        }
