"""
Phase 3 — Feature engineering (CORE + OPTIONAL) and
Phase 4 — Leakage prevention.

Every rolling/velocity feature here is computed using ONLY orders strictly
BEFORE the current one (by created_at, within the relevant grouping key).
This holds regardless of how the data is later split into train/val/test —
correct time-respecting aggregation is what actually prevents leakage, not
the split itself.

Leakage columns explicitly excluded from the final feature matrix, and why:
  - `status`      : the current order's own settlement outcome. In a real
                    deployment this fraud score would be computed at/near
                    checkout, before the charge is authorized and long
                    before any refund could occur. Several fraud archetypes
                    in this dataset are partly *defined* by their eventual
                    status (e.g. refund_abuse), which makes `status` a
                    near-tautological predictor if left in — a textbook
                    leakage case.
  - `has_qr_code` : only generated after a successful payment; same issue.
  - `fraud_type`  : synthetic debug/audit metadata, not a real signal.
  - identifiers   : order_id/user_id/event_id/tier_id/device_id/ip_address/
                    card_fingerprint/user_agent/created_at are used to
                    *compute* the features below, then dropped — high-
                    cardinality IDs are not fed to the model directly.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from ..app.services.fraud_detection import schema_contract as sc

logger = logging.getLogger("training_pipeline.feature_engineering")


def _rolling_prior_count_sum(
    df: pd.DataFrame, key_col: str, time_col: str, window: str, value_col: str | None = None
) -> pd.DataFrame:
    """
    For each row, count (and optionally sum value_col) of OTHER rows sharing
    the same key_col value within `window` immediately preceding it in time.
    Rows where key_col is null are returned as NaN (no signal available).
    Fully vectorized via groupby().rolling() — no per-row Python loops.
    """
    valid = df[df[key_col].notna()].copy()
    valid = valid.sort_values([key_col, time_col])
    valid = valid.set_index(time_col)

    grouped = valid.groupby(key_col, observed=True)
    count_incl_self = grouped["_row_id"].rolling(window).count()
    result = pd.DataFrame({"count_prior": count_incl_self.reset_index(level=0, drop=True) - 1})

    if value_col is not None:
        sum_incl_self = grouped[value_col].rolling(window).sum()
        result["sum_prior"] = (
            sum_incl_self.reset_index(level=0, drop=True) - valid[value_col].to_numpy()
        )

    result["_row_id"] = valid["_row_id"].to_numpy()
    result = result.set_index("_row_id").reindex(df["_row_id"])
    result.index = df.index
    return result


def _expanding_prior_rate(
    df: pd.DataFrame, key_col: str, time_col: str, flag_col: str
) -> pd.Series:
    """Expanding (all-time-prior) mean of a 0/1 flag, grouped by key_col, time-respecting."""
    valid_sorted = df.sort_values([key_col, time_col])
    grp = valid_sorted.groupby(key_col, observed=True)[flag_col]
    cum_sum = grp.cumsum() - valid_sorted[flag_col]
    cum_count = grp.cumcount()
    prior_rate = (cum_sum / cum_count.replace(0, np.nan)).fillna(0.0)
    return prior_rate.reindex(df.index)


def _first_occurrence_running_distinct(df: pd.DataFrame, group_col: str, item_col: str) -> pd.Series:
    """
    Vectorized running count of distinct `item_col` values seen so far
    within `group_col`, STRICTLY BEFORE the current row (time-respecting,
    df must already be sorted by [group_col, time]). Rows with a null
    item_col never introduce a "new" item.
    """
    has_item = df[item_col].notna()
    is_new = (~df.duplicated(subset=[group_col, item_col], keep="first")) & has_item
    cumulative_incl_self = is_new.groupby(df[group_col], observed=True).cumsum()
    return cumulative_incl_self - is_new.astype(int)


def engineer_core_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute every CORE_FEATURES column. Never touches optional raw columns."""
    df = df.sort_values(["user_id", "created_at"]).reset_index(drop=True)
    df["_row_id"] = np.arange(len(df))

    df["price_per_ticket"] = df["total_price"] / df["quantity"].replace(0, np.nan)
    df["price_deviation_from_listed"] = (df["price_per_ticket"] - df["tier_listed_price"]).fillna(0.0)

    df["account_age_days"] = (df["created_at"] - df["account_created_at"]).dt.total_seconds() / 86400
    df["purchase_hour"] = df["created_at"].dt.hour
    df["purchase_weekday"] = df["created_at"].dt.dayofweek
    df["purchase_month"] = df["created_at"].dt.month
    df["is_weekend"] = df["purchase_weekday"].isin([5, 6])
    df["is_late_night"] = df["purchase_hour"].between(0, 4)

    df["days_until_event"] = (df["start_datetime"] - df["created_at"]).dt.total_seconds() / 86400
    df["hours_since_tier_listed"] = (df["created_at"] - df["listed_at"]).dt.total_seconds() / 3600
    df["quantity_share_of_tier_capacity"] = df["quantity"] / df["total_seats"].replace(0, np.nan)

    # --- User velocity (time-respecting rolling windows, prior orders only) ---
    is_paid = (df["status"] == "paid").astype(int)
    is_refunded = (df["status"] == "refunded").astype(int)

    r1h = _rolling_prior_count_sum(df, "user_id", "created_at", "1h")
    r24h = _rolling_prior_count_sum(df, "user_id", "created_at", "24h", value_col="total_price")
    r7d = _rolling_prior_count_sum(df, "user_id", "created_at", "7D")

    df["purchases_last_1h"] = r1h["count_prior"].clip(lower=0).fillna(0).to_numpy()
    df["purchases_last_24h"] = r24h["count_prior"].clip(lower=0).fillna(0).to_numpy()
    df["spend_last_24h"] = r24h["sum_prior"].clip(lower=0).fillna(0).to_numpy()
    df["purchases_last_7d"] = r7d["count_prior"].clip(lower=0).fillna(0).to_numpy()

    r7d_spend = _rolling_prior_count_sum(df, "user_id", "created_at", "7D", value_col="total_price")
    df["spend_last_7d"] = r7d_spend["sum_prior"].clip(lower=0).fillna(0).to_numpy()

    # Distinct events touched in the last 24h: a true rolling-distinct-count
    # is expensive at this scale and, empirically, most purchase bursts in
    # this dataset concentrate on one event — so purchases_last_24h is used
    # directly as a (documented, deliberately simple) proxy rather than
    # computing a second, near-identical rolling-window statistic.
    df["distinct_events_last_24h"] = df["purchases_last_24h"]

    grp = df.groupby("user_id", observed=True)
    df["time_since_last_order_hours"] = (
        (df["created_at"] - grp["created_at"].shift(1)).dt.total_seconds() / 3600
    ).fillna(999.0).clip(lower=0)
    df["user_lifetime_order_count"] = grp.cumcount()
    df["is_first_order"] = df["user_lifetime_order_count"] == 0

    df["_is_paid_tmp"] = is_paid.to_numpy()
    df["_is_refunded_tmp"] = is_refunded.to_numpy()
    df["user_historical_paid_rate"] = _expanding_prior_rate(df, "user_id", "created_at", "_is_paid_tmp")
    df["user_historical_refund_rate"] = _expanding_prior_rate(df, "user_id", "created_at", "_is_refunded_tmp")

    # --- Event popularity (time-respecting: seats sold so far / capacity) ---
    event_qty = _rolling_prior_count_sum(
        df.assign(_v=df["quantity"]), "event_id", "created_at", "3650D", value_col="quantity"
    )
    df["event_popularity_ratio"] = (
        (event_qty["sum_prior"].clip(lower=0) / df["max_capacity"].replace(0, np.nan)).fillna(0.0).to_numpy()
    )

    # --- Organizer historical refund rate (expanding, prior only) ---
    df["organizer_historical_refund_rate"] = _expanding_prior_rate(
        df, "organizer_id", "created_at", "_is_refunded_tmp"
    )

    df = df.drop(columns=["_is_paid_tmp", "_is_refunded_tmp", "_row_id"], errors="ignore")
    return df


def engineer_optional_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute OPTIONAL_FEATURES that require the enrichment columns
    (device/network/payment/phone). Every computed column here degrades to
    NaN when its underlying raw enrichment data is absent for that row —
    align_to_schema() supplies the final default at preprocessing time.
    """
    df = df.sort_values(["user_id", "created_at"]).reset_index(drop=True)
    df["_row_id"] = np.arange(len(df))

    for key_col, out_col in [("device_id", "purchases_same_device_24h"),
                              ("ip_address", "purchases_same_ip_24h"),
                              ("card_fingerprint", "purchases_same_card_24h")]:
        r = _rolling_prior_count_sum(df, key_col, "created_at", "24h")
        df[out_col] = r["count_prior"].clip(lower=0).to_numpy()

    df["unique_devices_per_user"] = _first_occurrence_running_distinct(df, "user_id", "device_id")
    df["unique_cards_per_device"] = _first_occurrence_running_distinct(df, "device_id", "card_fingerprint")

    df["ip_event_country_mismatch"] = np.where(
        df["ip_country"].notna() & df["country"].notna(),
        (df["ip_country"].astype(str) != df["country"].astype(str)).astype(float),
        np.nan,
    )

    df = df.drop(columns=["_row_id"], errors="ignore")
    return df


def drop_leakage_and_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop everything in LEAKAGE_COLUMNS and IDENTIFIER_COLUMNS except the label."""
    cols_to_drop = [c for c in (sc.LEAKAGE_COLUMNS + sc.IDENTIFIER_COLUMNS) if c in df.columns and c != "is_fraud"]
    return df.drop(columns=cols_to_drop)


def build_feature_matrix(master_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Full Phase 3+4 pipeline: engineer core + optional features, then strip
    leakage/identifier columns. Returns (X, y) with X restricted to exactly
    CORE_FEATURES + OPTIONAL_FEATURES, in a fixed column order.
    """
    df = master_df.copy()
    df = engineer_core_features(df)
    df = engineer_optional_features(df)

    y = df["is_fraud"].astype(int).reset_index(drop=True)
    keep_cols = sc.CORE_FEATURES + sc.OPTIONAL_FEATURES
    X = df[keep_cols].reset_index(drop=True)

    logger.info("Feature matrix built: %s rows, %s features (%s core, %s optional)",
                X.shape[0], X.shape[1], len(sc.CORE_FEATURES), len(sc.OPTIONAL_FEATURES))
    return X, y
