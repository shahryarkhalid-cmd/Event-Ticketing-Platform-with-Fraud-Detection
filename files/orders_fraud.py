"""
Generation of fraudulent order archetypes.

Each function generates a behaviorally distinct fraud pattern using only
fields that exist on the real Order/User/Event/TicketTier tables. Patterns
are generated as *distributions*, not hard rules, and deliberately overlap
with legitimate behavior so a model has to learn interacting signals rather
than memorize a single-feature threshold.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config
from .order_utils import build_listing_table, sample_status

logger = logging.getLogger("dataset_generator.orders_fraud")


def bot_card_testing(rng, customers_df, events_df, tiers_df, n_bursts: int) -> pd.DataFrame:
    """
    Bot / card-testing bursts: many rapid, low-quantity orders across many
    different events/tiers in a tight time window, skewed toward new,
    unverified accounts (cheap to create, easy to abandon).
    """
    listing = build_listing_table(events_df, tiers_df)
    candidates = customers_df.copy()
    weight = np.where(candidates["is_verified"], 0.3, 1.0)
    weight = weight / weight.sum()
    attackers = candidates.sample(
        n=min(n_bursts, len(candidates)), weights=weight,
        random_state=int(rng.integers(0, 1_000_000)),
    )

    rows = []
    for _, u in attackers.iterrows():
        burst_size = int(rng.integers(6, 24))
        burst_start_low = max(u["account_created_at"], pd.Timestamp(config.PLATFORM_START))
        burst_start_high = pd.Timestamp(config.PLATFORM_NOW) - pd.Timedelta(hours=2)
        if burst_start_low >= burst_start_high:
            continue
        burst_start = burst_start_low + (burst_start_high - burst_start_low) * rng.random()

        pool = listing[(listing["listed_at"] <= burst_start) & (listing["start_datetime"] >= burst_start)]
        if len(pool) < 3:
            pool = listing
        picks = pool.sample(n=min(burst_size, len(pool)), replace=True, random_state=int(rng.integers(0, 1_000_000)))

        offsets_minutes = np.sort(rng.uniform(0, rng.uniform(3, 45), size=len(picks)))
        for (_, tier), off in zip(picks.iterrows(), offsets_minutes):
            rows.append(
                {
                    "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                    "quantity": 1, "unit_price": tier["price"],
                    "created_at": burst_start + pd.Timedelta(minutes=float(off)),
                    "fraud_type": "bot_card_testing", "is_fraud": True,
                }
            )

    df = pd.DataFrame(rows)
    if len(df):
        df["status"] = rng.choice(["pending", "paid", "refunded"], size=len(df), p=[0.55, 0.30, 0.15])
    logger.info("Generated bot_card_testing orders: %s (from %s attackers)", len(df), len(attackers))
    return df


def scalping_bulk(rng, customers_df, events_df, tiers_df, n_orders: int) -> pd.DataFrame:
    """
    Scalping: large bulk purchases (a sizeable share of a tier's inventory),
    concentrated right after tickets go on sale for in-demand events.
    """
    listing = build_listing_table(events_df, tiers_df)
    # Prefer smaller-capacity / higher-demand-looking tiers (easier to corner)
    small_tier_pool = listing[listing["total_seats"] < listing["total_seats"].median() * 1.5]
    pool = small_tier_pool if len(small_tier_pool) > 20 else listing

    attackers = customers_df.sample(n=min(n_orders, len(customers_df)), random_state=int(rng.integers(0, 1_000_000)))
    picks = pool.sample(n=len(attackers), replace=True, random_state=int(rng.integers(0, 1_000_000)))

    rows = []
    for (_, u), (_, tier) in zip(attackers.iterrows(), picks.iterrows()):
        quantity = int(np.clip(rng.integers(10, 45), 1, max(2, int(tier["total_seats"] * 0.55))))
        # Buy within the first few hours of the on-sale window
        purchase_time = tier["listed_at"] + pd.Timedelta(minutes=float(rng.exponential(90)))
        purchase_time = min(purchase_time, tier["start_datetime"] - pd.Timedelta(hours=1))
        rows.append(
            {
                "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                "quantity": quantity, "unit_price": tier["price"], "created_at": purchase_time,
                "fraud_type": "scalping_bulk", "is_fraud": True,
            }
        )

    df = pd.DataFrame(rows)
    if len(df):
        df["status"] = rng.choice(["paid", "refunded", "pending"], size=len(df), p=[0.68, 0.20, 0.12])
    logger.info("Generated scalping_bulk orders: %s", len(df))
    return df


def account_takeover(rng, customers_df, events_df, tiers_df, n_accounts: int):
    """
    Account takeover: an established account with a quiet, normal order
    history suddenly places one abnormally large/expensive order after a
    gap, often at an unusual hour. Returns (history_df, spike_df) — the
    history rows are legitimate, only the spike row is fraud.
    """
    listing = build_listing_table(events_df, tiers_df)
    established = customers_df[
        customers_df["account_created_at"] < (pd.Timestamp(config.PLATFORM_NOW) - pd.Timedelta(days=60))
    ]
    if established.empty:
        established = customers_df
    victims = established.sample(n=min(n_accounts, len(established)), random_state=int(rng.integers(0, 1_000_000)))

    history_rows, spike_rows = [], []
    for _, u in victims.iterrows():
        n_hist = int(rng.integers(2, 6))
        hist_picks = listing.sample(n=min(n_hist, len(listing)), random_state=int(rng.integers(0, 1_000_000)))
        last_time = u["account_created_at"] + pd.Timedelta(days=int(rng.integers(5, 40)))
        for _, tier in hist_picks.iterrows():
            t = max(last_time, tier["listed_at"])
            t = min(t, tier["start_datetime"] - pd.Timedelta(hours=2))
            history_rows.append(
                {
                    "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                    "quantity": int(rng.choice([1, 2])), "unit_price": tier["price"], "created_at": t,
                    "fraud_type": "none", "is_fraud": False,
                }
            )
            last_time = t + pd.Timedelta(days=int(rng.integers(3, 25)))

        # The takeover spike, well after the quiet history, at an odd hour
        spike_tier = listing.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        gap_days = int(rng.integers(20, 90))
        spike_time = last_time + pd.Timedelta(days=gap_days)
        spike_time = min(max(spike_time, spike_tier["listed_at"]), spike_tier["start_datetime"] - pd.Timedelta(hours=1))
        spike_hour = int(rng.choice([0, 1, 2, 3, 4], p=[0.3, 0.25, 0.2, 0.15, 0.1]))
        spike_time = spike_time.floor("D") + pd.Timedelta(hours=spike_hour, minutes=int(rng.integers(0, 60)))
        quantity = int(rng.integers(4, 12))
        spike_rows.append(
            {
                "user_id": u["user_id"], "event_id": spike_tier["event_id"], "tier_id": spike_tier["tier_id"],
                "quantity": quantity, "unit_price": spike_tier["price"], "created_at": spike_time,
                "fraud_type": "account_takeover", "is_fraud": True,
            }
        )

    history_df = pd.DataFrame(history_rows)
    spike_df = pd.DataFrame(spike_rows)
    if len(history_df):
        history_df["status"] = sample_status(rng, len(history_df), refund_rate=0.03, pending_rate=0.03)
    if len(spike_df):
        spike_df["status"] = rng.choice(["paid", "pending"], size=len(spike_df), p=[0.75, 0.25])
    logger.info(
        "Generated account_takeover: %s history orders (legit) + %s spike orders (fraud)",
        len(history_df), len(spike_df),
    )
    return history_df, spike_df


def refund_abuse(rng, customers_df, events_df, tiers_df, n_accounts: int) -> pd.DataFrame:
    """
    Friendly-fraud / refund abuse: a chronically high personal refund rate
    across several otherwise unremarkable orders.
    """
    listing = build_listing_table(events_df, tiers_df)
    abusers = customers_df.sample(n=min(n_accounts, len(customers_df)), random_state=int(rng.integers(0, 1_000_000)))

    rows = []
    for _, u in abusers.iterrows():
        n_orders = int(rng.integers(2, 7))
        picks = listing.sample(n=min(n_orders, len(listing)), random_state=int(rng.integers(0, 1_000_000)))
        t = max(u["account_created_at"], pd.Timestamp(config.PLATFORM_START)) + pd.Timedelta(days=int(rng.integers(1, 60)))
        for _, tier in picks.iterrows():
            t = max(t, tier["listed_at"])
            t = min(t, tier["start_datetime"] - pd.Timedelta(hours=1))
            rows.append(
                {
                    "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                    "quantity": int(rng.choice([1, 2, 3])), "unit_price": tier["price"], "created_at": t,
                    "fraud_type": "refund_abuse", "is_fraud": True,
                }
            )
            t = t + pd.Timedelta(days=int(rng.integers(2, 20)))

    df = pd.DataFrame(rows)
    if len(df):
        # The defining trait: most of THEIR orders end up refunded
        df["status"] = rng.choice(["refunded", "paid"], size=len(df), p=[0.72, 0.28])
    logger.info("Generated refund_abuse orders: %s (from %s accounts)", len(df), len(abusers))
    return df


def new_account_high_value(rng, customers_df, events_df, tiers_df, n_orders: int) -> pd.DataFrame:
    """
    Brand-new, unverified account placing one unusually large first order
    almost immediately after registering — classic stolen-card pattern.
    """
    listing = build_listing_table(events_df, tiers_df)
    fresh = customers_df[~customers_df["is_verified"]]
    if fresh.empty:
        fresh = customers_df
    attackers = fresh.sample(n=min(n_orders, len(fresh)), random_state=int(rng.integers(0, 1_000_000)))

    rows = []
    for _, u in attackers.iterrows():
        tier = listing.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        earliest = max(u["account_created_at"], tier["listed_at"])
        latest = tier["start_datetime"] - pd.Timedelta(hours=1)
        if earliest >= latest:
            continue
        # Within hours of account creation
        t = u["account_created_at"] + pd.Timedelta(minutes=float(rng.exponential(180)))
        t = min(max(t, earliest), latest)
        quantity = int(rng.integers(4, 15))
        rows.append(
            {
                "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                "quantity": quantity, "unit_price": tier["price"], "created_at": t,
                "fraud_type": "new_account_high_value", "is_fraud": True,
            }
        )

    df = pd.DataFrame(rows)
    if len(df):
        df["status"] = rng.choice(["paid", "pending", "refunded"], size=len(df), p=[0.55, 0.30, 0.15])
    logger.info("Generated new_account_high_value orders: %s", len(df))
    return df


def stealth_fraud(rng, customers_df, events_df, tiers_df, n_orders: int) -> pd.DataFrame:
    """
    Stealth fraud: ordinary-looking single orders (typical quantity, typical
    price, typical hour, sometimes even a verified account) that are still
    fraudulent — representing fraud that isn't cleanly separable from the
    transactional signals available here (e.g. identity theft on an
    otherwise-normal-looking account). Keeps the classification problem
    honestly difficult rather than trivially separable.
    """
    listing = build_listing_table(events_df, tiers_df)
    attackers = customers_df.sample(n=min(n_orders, len(customers_df)), random_state=int(rng.integers(0, 1_000_000)))
    picks = listing.sample(n=len(attackers), replace=True, random_state=int(rng.integers(0, 1_000_000)))

    rows = []
    for (_, u), (_, tier) in zip(attackers.iterrows(), picks.iterrows()):
        earliest = max(u["account_created_at"], tier["listed_at"])
        latest = tier["start_datetime"] - pd.Timedelta(hours=1)
        if earliest >= latest:
            continue
        t = earliest + (latest - earliest) * rng.random()
        quantity = int(rng.choice([1, 2], p=[0.75, 0.25]))
        rows.append(
            {
                "user_id": u["user_id"], "event_id": tier["event_id"], "tier_id": tier["tier_id"],
                "quantity": quantity, "unit_price": tier["price"], "created_at": t,
                "fraud_type": "stealth_fraud", "is_fraud": True,
            }
        )

    df = pd.DataFrame(rows)
    if len(df):
        df["status"] = rng.choice(["paid", "pending"], size=len(df), p=[0.8, 0.2])
    logger.info("Generated stealth_fraud orders: %s", len(df))
    return df
