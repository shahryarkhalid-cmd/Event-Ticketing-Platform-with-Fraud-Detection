"""
Phase 2 — Merge the normalized CSVs into a single master dataset, one row
per completed/attempted order.

Joins: orders -> ticket_tiers -> events (+ organizer risk via events) ,
       orders -> users, orders -> order_enrichment (left join; may be
       entirely absent for a row by design).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("training_pipeline.merge")


def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Downcast numerics and convert low-cardinality object columns to category."""
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")
    for col in df.select_dtypes(include=["object"]).columns:
        n_unique = df[col].nunique(dropna=True)
        if n_unique and n_unique / max(len(df), 1) < 0.5:
            df[col] = df[col].astype("category")
    return df


def load_raw_tables(data_dir: Path) -> dict[str, pd.DataFrame]:
    """Load all four source CSVs with explicit dtypes/parsing, log shapes."""
    users = pd.read_csv(data_dir / "users.csv", parse_dates=["account_created_at"])
    events = pd.read_csv(data_dir / "events.csv", parse_dates=["listed_at", "start_datetime", "end_datetime"])
    tiers = pd.read_csv(data_dir / "ticket_tiers.csv")
    orders = pd.read_csv(data_dir / "orders.csv", parse_dates=["created_at"])
    enrichment = pd.read_csv(data_dir / "order_enrichment.csv")

    for name, df in [("users", users), ("events", events), ("ticket_tiers", tiers),
                      ("orders", orders), ("order_enrichment", enrichment)]:
        logger.info("Loaded %s: %s rows, %s cols", name, *df.shape)

    return {"users": users, "events": events, "tiers": tiers, "orders": orders, "enrichment": enrichment}


def merge_master_dataset(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build the one-row-per-order master dataset. Keeps raw identifiers and
    raw timestamps in the output — feature_engineering.py consumes those
    and drops them again before modeling (see schema_contract.IDENTIFIER_COLUMNS).
    """
    orders, users, events, tiers, enrichment = (
        tables["orders"], tables["users"], tables["events"], tables["tiers"], tables["enrichment"]
    )

    before = len(orders)
    n_dupe = orders.duplicated(subset=["order_id"]).sum()
    if n_dupe:
        orders = orders.drop_duplicates(subset=["order_id"], keep="first")
        logger.warning("Dropped %s duplicate order_id rows", n_dupe)

    df = orders.merge(
        tiers.rename(columns={"price": "tier_listed_price"}), on="tier_id", how="left",
        validate="many_to_one", suffixes=("", "_tier"),
    )
    if "event_id_tier" in df.columns:
        df = df.drop(columns=["event_id_tier"])

    df = df.merge(
        events.rename(columns={"category": "event_category"}), on="event_id", how="left",
        validate="many_to_one", suffixes=("", "_event"),
    )
    df = df.merge(users, on="user_id", how="left", validate="many_to_one", suffixes=("", "_user"))

    # The orders table carries reserved, always-null placeholders for
    # ip_address/user_agent/device_id (see Stage-1 SCHEMA.md forward-compat
    # hooks) — the real optional signal comes from order_enrichment.csv.
    # Drop the placeholders here so the merge has one clean copy of each.
    df = df.drop(columns=["ip_address", "user_agent", "device_id"], errors="ignore")
    df = df.merge(enrichment, on="order_id", how="left", validate="one_to_one")

    assert len(df) == before - n_dupe, "Row count changed unexpectedly during merge — check join keys"

    df = _optimize_dtypes(df)
    logger.info("Merged master dataset: %s rows, %s cols, %.1f MB", *df.shape, df.memory_usage(deep=True).sum() / 1e6)
    return df


def build_and_save(data_dir: Path, output_path: Path) -> pd.DataFrame:
    tables = load_raw_tables(data_dir)
    master = merge_master_dataset(tables)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    master.to_parquet(output_path, index=False)
    logger.info("Saved master dataset to %s", output_path)
    return master
