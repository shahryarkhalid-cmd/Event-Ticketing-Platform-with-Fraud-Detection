"""Generation of the legitimate order population (the majority class)."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config
from .order_utils import build_listing_table, sample_purchase_time, apply_hour_bias, sample_status

logger = logging.getLogger("dataset_generator.orders_legit")


def generate_legitimate_orders(
    rng: np.random.Generator,
    customers_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tiers_df: pd.DataFrame,
    target_count: int,
) -> pd.DataFrame:
    """
    Generate the baseline legitimate order population.

    Order count per customer follows a mixture: most customers place 0-3
    orders, a small "regulars" segment places many more (power-law-ish),
    which is what real ticketing platforms look like.
    """
    listing = build_listing_table(events_df, tiers_df)
    customer_ids = customers_df["user_id"].to_numpy()
    account_created = customers_df.set_index("user_id")["account_created_at"]

    is_power_user = rng.random(len(customer_ids)) < 0.06
    order_counts = np.where(
        is_power_user,
        rng.poisson(6.5, size=len(customer_ids)) + 1,
        rng.poisson(1.15, size=len(customer_ids)),
    )

    # Scale so the total roughly matches target_count
    scale = target_count / max(order_counts.sum(), 1)
    order_counts = np.maximum(0, np.round(order_counts * scale)).astype(int)

    rows = []
    for uid, n_orders in zip(customer_ids, order_counts):
        if n_orders == 0:
            continue
        acct_created = account_created.loc[uid]
        # Each customer's orders concentrate in a handful of categories they like
        preferred_categories = rng.choice(
            config.EVENT_CATEGORIES, size=rng.integers(1, 4), replace=False
        )
        candidate_pool = listing[listing["category"].isin(preferred_categories)]
        if candidate_pool.empty:
            candidate_pool = listing
        # Only tiers listed after the account existed
        candidate_pool = candidate_pool[candidate_pool["listed_at"] >= acct_created - pd.Timedelta(days=1)]
        if candidate_pool.empty:
            continue

        picks = candidate_pool.sample(n=min(n_orders, len(candidate_pool)), replace=True, random_state=int(rng.integers(0, 1_000_000)))
        for _, tier in picks.iterrows():
            purchase_time = sample_purchase_time(rng, tier["listed_at"], tier["start_datetime"])
            purchase_time = max(purchase_time, acct_created + pd.Timedelta(minutes=5))
            quantity = int(rng.choice([1, 1, 1, 2, 2, 3, 4], p=[0.42, 0.0, 0.0, 0.28, 0.0, 0.18, 0.12]))
            rows.append(
                {
                    "user_id": uid,
                    "event_id": tier["event_id"],
                    "tier_id": tier["tier_id"],
                    "quantity": quantity,
                    "unit_price": tier["price"],
                    "created_at_raw": purchase_time,
                    "fraud_type": "none",
                    "is_fraud": False,
                }
            )

    df = pd.DataFrame(rows)
    df["created_at"] = apply_hour_bias(rng, df["created_at_raw"], late_night_weight=0.018)
    df["status"] = sample_status(rng, len(df), refund_rate=0.045, pending_rate=0.04)
    df = df.drop(columns=["created_at_raw"])
    logger.info("Generated legitimate baseline orders: %s (target was %s)", len(df), target_count)
    return df


def generate_legitimate_exceptions(
    rng: np.random.Generator,
    customers_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tiers_df: pd.DataFrame,
    n_bulk: int,
    n_late_night: int,
) -> pd.DataFrame:
    """
    Generate deliberately "fraud-shaped but legitimate" orders: hard negatives
    so the model can't just memorize thresholds like "large quantity = fraud"
    or "late night = fraud".

    - Bulk legitimate buyers: established, verified accounts buying a large
      quantity in one order (office outing, family reunion, tour group).
    - Legitimate late-night buyers: verified accounts purchasing immediately
      when a popular event goes on sale (genuine enthusiasts), which happens
      to land at an unusual hour.
    """
    listing = build_listing_table(events_df, tiers_df)
    established = customers_df[
        customers_df["account_created_at"] < (pd.Timestamp(config.PLATFORM_NOW) - pd.Timedelta(days=90))
    ]
    established = established[established["is_verified"]]
    if established.empty:
        established = customers_df

    rows = []
    # --- Bulk legitimate buyers ---
    bulk_users = established.sample(n=min(n_bulk, len(established)), random_state=int(rng.integers(0, 1_000_000)))
    for _, u in bulk_users.iterrows():
        tier = listing.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        quantity = int(rng.integers(8, min(26, max(9, int(tier["total_seats"] * 0.3)))))
        purchase_time = sample_purchase_time(rng, tier["listed_at"], tier["start_datetime"])
        rows.append(
            {
                "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                "quantity": quantity, "unit_price": tier["price"], "created_at": purchase_time,
                "fraud_type": "none", "is_fraud": False,
            }
        )

    # --- Legitimate late-night on-sale rush buyers ---
    late_users = established.sample(n=min(n_late_night, len(established)), random_state=int(rng.integers(0, 1_000_000)))
    for _, u in late_users.iterrows():
        tier = listing.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        # Buy within the first hour of listing, regardless of clock hour
        purchase_time = tier["listed_at"] + pd.Timedelta(minutes=int(rng.integers(1, 55)))
        quantity = int(rng.choice([1, 2], p=[0.7, 0.3]))
        rows.append(
            {
                "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                "quantity": quantity, "unit_price": tier["price"], "created_at": purchase_time,
                "fraud_type": "none", "is_fraud": False,
            }
        )

    df = pd.DataFrame(rows)
    df["status"] = sample_status(rng, len(df), refund_rate=0.02, pending_rate=0.02)
    logger.info("Generated legitimate exception orders (hard negatives): %s", len(df))
    return df
