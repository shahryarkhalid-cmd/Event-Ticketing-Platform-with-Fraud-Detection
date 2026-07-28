"""Configuration for the fraud detection service.

All settings are environment-driven with sensible defaults.
To swap the model, you only need to update MODEL_PATH and
PREPROCESSING_PATH (or set the env vars) plus adjust
FEATURE_BUILDER_MODULE if the new model expects different features.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

# Directory containing this file — deployment artifacts live here
_FRAUD_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class FraudDetectionConfig:
    """Immutable configuration for the fraud detection service.

    Override any field via environment variables:
        FRAUD_MODEL_PATH          – path to the trained model pickle
        FRAUD_PREPROCESSING_PATH  – path to preprocessing artifacts pickle
        FRAUD_THRESHOLD           – probability threshold for fraud flagging
        FRAUD_FLAG_STATUS         – order status when flagged as fraud
        FRAUD_ENABLED             – "true"/"false" to toggle the service
        FRAUD_MODEL_NAME          – human-readable model identifier
        FRAUD_FALLBACK_ON_ERROR   – "true"/"false" fail-open behaviour
    """

    # ── Model paths ───────────────────────────────────────────────
    model_path: str = field(
        default_factory=lambda: os.getenv(
            "FRAUD_MODEL_PATH",
            str(_FRAUD_DIR / "best_model.pkl"),
        )
    )
    preprocessing_path: str = field(
        default_factory=lambda: os.getenv(
            "FRAUD_PREPROCESSING_PATH",
            str(_FRAUD_DIR / "preprocessor.pkl"),
        )
    )

    # ── Prediction behaviour ──────────────────────────────────────
    threshold: float = field(
        default_factory=lambda: float(os.getenv("FRAUD_THRESHOLD", "0.5"))
    )
    flag_status: str = field(
        default_factory=lambda: os.getenv("FRAUD_FLAG_STATUS", "fraud_review")
    )
    enabled: bool = field(
        default_factory=lambda: os.getenv("FRAUD_ENABLED", "true").lower() == "true"
    )
    fallback_on_error: bool = field(
        default_factory=lambda: os.getenv(
            "FRAUD_FALLBACK_ON_ERROR", "true"
        ).lower()
        == "true"
    )

    # ── Metadata ──────────────────────────────────────────────────
    model_name: str = field(
        default_factory=lambda: os.getenv("FRAUD_MODEL_NAME", "Tixora_XGBoost")
    )

    # ── Core features expected by the trained model ───────────────
    # Single source of truth — must match feature_list.json core_features.
    APP_SCHEMA_FEATURES: List[str] = field(default_factory=lambda: [
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
        "is_verified",
        "is_active",
        "is_first_order",
        "is_weekend",
        "is_late_night",
        "event_category",
    ])


# Module-level singleton — import this wherever config is needed
fraud_config = FraudDetectionConfig()
