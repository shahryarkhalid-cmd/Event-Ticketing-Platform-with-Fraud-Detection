"""
Tixora Fraud Detection — Synthetic Dataset Generator (Phase 3)
================================================================
Generates four normalized CSV tables mirroring the real application schema
(app/models/Users.py, Event.py, Ticket.py, Orders.py) plus a synthetic
`is_fraud` label on the orders table.

Run:
    python -m data_generation.generate_dataset

Design principles (see ../SCHEMA.md for the full write-up):
  * Only fields that exist in the live app are used as real signal.
  * IP/device/geolocation are represented as reserved, all-null columns so
    the pipeline can accept them later without a redesign.
  * Fraud is generated as overlapping behavioral distributions per archetype,
    not hard thresholds, and includes deliberate "legitimate exceptions"
    (hard negatives) so a model can't shortcut on a single feature.
  * Fixed random seed -> fully reproducible.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .entities import generate_users, generate_events, generate_ticket_tiers
from .orders_legit import generate_legitimate_orders, generate_legitimate_exceptions
from .orders_fraud import (
    bot_card_testing, scalping_bulk, account_takeover,
    refund_abuse, new_account_high_value, stealth_fraud,
)


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("dataset_generator")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    fh = logging.FileHandler(config.LOG_DIR / "dataset_generation.log", mode="w")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


def clamp_timestamps(orders: pd.DataFrame, events: pd.DataFrame, tiers: pd.DataFrame,
                      users: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Defensive data-validation pass: a handful of orders from the archetype
    generators can land a few minutes outside their tier's sale window
    (edge cases from independently randomized sub-generators). Clamp into
    the event's sale window first (a hard physical constraint — you can't
    buy a ticket outside its sale window), then drop the small residual of
    rows where the buyer's account genuinely didn't exist yet at any point
    during that window (a referential mismatch from independent random
    sampling, not something that can be clamped away safely).
    """
    ctx = orders.merge(
        tiers[["tier_id", "event_id"]].merge(
            events[["event_id", "listed_at", "start_datetime"]], on="event_id"
        ),
        on=["tier_id", "event_id"], how="left",
    ).merge(users[["user_id", "account_created_at"]], on="user_id", how="left")

    before = ctx["created_at"].copy()
    clamped = ctx["created_at"].clip(lower=ctx["listed_at"] + pd.Timedelta(minutes=1), upper=ctx["start_datetime"])
    n_changed = int((clamped != before).sum())

    orders = orders.copy()
    orders["created_at"] = clamped.values
    logger.info("Timestamp validation: clamped %s / %s orders into their event's sale window.", n_changed, len(orders))

    still_invalid = clamped.values < ctx["account_created_at"].values
    n_invalid = int(still_invalid.sum())
    if n_invalid:
        orders = orders.loc[~still_invalid].reset_index(drop=True)
        logger.info(
            "Dropped %s orders (%.3f%%) where the buyer's account did not exist during "
            "the event's entire sale window (referential mismatch from independent random "
            "sampling across generators, not a recoverable timestamp).",
            n_invalid, 100 * n_invalid / len(clamped),
        )
    return orders


def assemble_orders(rng: np.random.Generator, fragments: list[pd.DataFrame],
                     events: pd.DataFrame, tiers: pd.DataFrame, users: pd.DataFrame,
                     logger: logging.Logger) -> pd.DataFrame:
    """Concatenate every order fragment, validate, and assign sequential IDs."""
    fragments = [f for f in fragments if f is not None and len(f)]
    orders = pd.concat(fragments, ignore_index=True, sort=False)

    # Fidelity to app.services.Order_services.book_ticket: total_price = tier.price * quantity
    orders["total_price"] = (orders["unit_price"] * orders["quantity"]).round(2)
    orders = orders.drop(columns=["unit_price"])

    orders = clamp_timestamps(orders, events, tiers, users, logger)
    orders = orders.sort_values("created_at").reset_index(drop=True)
    orders.insert(0, "order_id", np.arange(1, len(orders) + 1))

    orders["has_qr_code"] = orders["status"].eq("paid") & (rng.random(len(orders)) < 0.97)

    # Forward-compatibility placeholders — see SCHEMA.md. Populated as null;
    # the feature-engineering "network" feature group is a documented no-op
    # until these are actually captured by the application.
    orders["ip_address"] = pd.NA
    orders["user_agent"] = pd.NA
    orders["device_id"] = pd.NA

    ordered_cols = [
        "order_id", "user_id", "event_id", "tier_id", "quantity", "total_price",
        "status", "created_at", "has_qr_code",
        "ip_address", "user_agent", "device_id",
        "is_fraud", "fraud_type",
    ]
    return orders[ordered_cols]


def validate_dataset(users, events, tiers, orders, logger: logging.Logger) -> None:
    """Referential-integrity and sanity checks before writing to disk."""
    assert orders["user_id"].isin(users.loc[users["role"] == "customer", "user_id"]).all(), \
        "Found an order placed by a non-customer or unknown user_id"
    assert orders["event_id"].isin(events["event_id"]).all(), "Order references unknown event_id"
    assert orders["tier_id"].isin(tiers["tier_id"]).all(), "Order references unknown tier_id"
    assert (orders["quantity"] > 0).all(), "Found non-positive quantity"
    assert (orders["total_price"] >= 0).all(), "Found negative total_price"
    assert orders["status"].isin(["pending", "paid", "refunded"]).all(), "Unexpected status value"
    assert orders["order_id"].is_unique, "Duplicate order_id"

    dup = orders.duplicated(subset=["user_id", "event_id", "tier_id", "created_at"]).sum()
    n_missing = orders.isna().sum()
    fraud_rate = orders["is_fraud"].mean()

    logger.info("Validation passed. %s exact-duplicate rows (kept, plausible for bot bursts).", dup)
    logger.info("Missing values per column:\n%s", n_missing[n_missing > 0])
    logger.info("Overall fraud rate: %.3f%% (%s / %s orders)", fraud_rate * 100, orders["is_fraud"].sum(), len(orders))
    logger.info("Fraud type breakdown:\n%s", orders.loc[orders["is_fraud"], "fraud_type"].value_counts())


def main() -> None:
    logger = configure_logging()
    t0 = time.time()
    rng = np.random.default_rng(config.RANDOM_STATE)
    logger.info("Starting synthetic dataset generation (seed=%s)", config.RANDOM_STATE)

    # --- Entities ---
    users = generate_users(rng)
    events = generate_events(rng, users)
    tiers = generate_ticket_tiers(rng, events)
    customers = users[users["role"] == "customer"].reset_index(drop=True)

    # --- Legitimate baseline ---
    legit_target = int(config.TARGET_N_ORDERS * (1 - config.TARGET_FRAUD_RATE) * 0.94)
    legit = generate_legitimate_orders(rng, customers, events, tiers, legit_target)
    legit_exceptions = generate_legitimate_exceptions(
        rng, customers, events, tiers, n_bulk=550, n_late_night=550
    )

    # --- Fraud archetypes ---
    bot_df = bot_card_testing(rng, customers, events, tiers, n_bursts=18)
    scalp_df = scalping_bulk(rng, customers, events, tiers, n_orders=150)
    ato_history_df, ato_spike_df = account_takeover(rng, customers, events, tiers, n_accounts=95)
    refund_df = refund_abuse(rng, customers, events, tiers, n_accounts=60)
    new_acct_df = new_account_high_value(rng, customers, events, tiers, n_orders=950)
    stealth_df = stealth_fraud(rng, customers, events, tiers, n_orders=750)

    orders = assemble_orders(
        rng,
        [legit, legit_exceptions, bot_df, scalp_df, ato_history_df, ato_spike_df,
         refund_df, new_acct_df, stealth_df],
        events, tiers, users, logger,
    )

    validate_dataset(users, events, tiers, orders, logger)

    # --- Persist ---
    users.to_csv(config.DATA_DIR / "users.csv", index=False)
    events.to_csv(config.DATA_DIR / "events.csv", index=False)
    tiers.to_csv(config.DATA_DIR / "ticket_tiers.csv", index=False)
    orders.to_csv(config.DATA_DIR / "orders.csv", index=False)

    elapsed = time.time() - t0
    logger.info("Done in %.1fs. Files written to %s", elapsed, config.DATA_DIR)
    logger.info(
        "Row counts — users: %s, events: %s, ticket_tiers: %s, orders: %s",
        len(users), len(events), len(tiers), len(orders),
    )


if __name__ == "__main__":
    main()
