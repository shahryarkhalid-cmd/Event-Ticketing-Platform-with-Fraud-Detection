"""Shared helpers for generating Order rows (app.models.Orders.Order)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_listing_table(events_df: pd.DataFrame, tiers_df: pd.DataFrame) -> pd.DataFrame:
    """Join tiers with their parent event's sale window for fast sampling."""
    listing = tiers_df.merge(
        events_df[["event_id", "organizer_id", "category", "listed_at", "start_datetime"]],
        on="event_id",
        how="left",
    )
    listing["window_seconds"] = (
        listing["start_datetime"] - listing["listed_at"]
    ).dt.total_seconds().clip(lower=3600)
    return listing


def sample_purchase_time(
    rng: np.random.Generator, listed_at: pd.Timestamp, start_datetime: pd.Timestamp
) -> pd.Timestamp:
    """
    Sample a purchase timestamp inside [listed_at, start_datetime] using a
    bimodal distribution: an early "on-sale rush" and a "last-minute" spike,
    with a quieter middle period. Mirrors real ticket-buying behavior.
    """
    window = (start_datetime - listed_at).total_seconds()
    window = max(window, 3600.0)

    if rng.random() < 0.35:
        frac = rng.beta(1.5, 9.0)   # early rush, close to 0
    elif rng.random() < 0.55:
        frac = rng.beta(9.0, 1.4)   # last-minute rush, close to 1
    else:
        frac = rng.beta(2.2, 2.2)   # broad middle

    frac = float(np.clip(frac, 0.0, 0.999))
    return listed_at + pd.Timedelta(seconds=frac * window)


def sample_hour_bias(rng: np.random.Generator, n: int, late_night_weight: float = 0.04) -> np.ndarray:
    """
    Sample an hour-of-day offset (0-23) biased toward daytime/evening,
    with a configurable small tail probability of late-night (0-5am) hours.
    """
    hours = np.arange(24)
    # Baseline weight: low overnight, rising through the day, peak evening
    base_weights = np.array(
        [0.5, 0.3, 0.2, 0.15, 0.15, 0.3, 0.6, 1.0, 1.3, 1.4, 1.4, 1.5,
         1.6, 1.6, 1.5, 1.5, 1.6, 1.8, 2.2, 2.6, 2.4, 2.0, 1.4, 0.8]
    )
    weights = base_weights.copy()
    weights[0:5] *= (late_night_weight / 0.02)  # scale up/down the overnight slice
    weights = weights / weights.sum()
    return rng.choice(hours, size=n, p=weights)


def apply_hour_bias(rng: np.random.Generator, timestamps: pd.Series, late_night_weight: float = 0.04) -> pd.Series:
    """Rewrite the hour component of each timestamp using sample_hour_bias."""
    hours = sample_hour_bias(rng, len(timestamps), late_night_weight)
    minutes = rng.integers(0, 60, size=len(timestamps))
    dates = timestamps.dt.floor("D")
    return dates + pd.to_timedelta(hours, unit="h") + pd.to_timedelta(minutes, unit="m")


def sample_status(rng: np.random.Generator, n: int, refund_rate: float = 0.05, pending_rate: float = 0.05) -> np.ndarray:
    paid_rate = max(0.0, 1.0 - refund_rate - pending_rate)
    return rng.choice(
        ["paid", "refunded", "pending"], size=n, p=[paid_rate, refund_rate, pending_rate]
    )
