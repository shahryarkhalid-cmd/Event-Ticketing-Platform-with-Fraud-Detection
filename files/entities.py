"""
Generation of the "slow-moving" entity tables: users, events, ticket tiers.

These mirror app/models/Users.py, app/models/Event.py, and app/models/Ticket.py
respectively. Only fields that exist on the real SQLModel tables are generated.
"""
from __future__ import annotations

import logging
from datetime import timedelta

import numpy as np
import pandas as pd

from . import config

logger = logging.getLogger("dataset_generator.entities")


def _random_timestamps(rng: np.random.Generator, start, end, n: int) -> pd.Series:
    """Uniformly random datetimes between start and end (inclusive)."""
    start_ts = pd.Timestamp(start).value
    end_ts = pd.Timestamp(end).value
    draws = rng.integers(start_ts, end_ts, size=n, dtype=np.int64)
    return pd.to_datetime(draws)


def generate_users(rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate the users table: N_ORGANIZERS organizer accounts + N_CUSTOMERS
    customer accounts, matching app.models.Users.User.

    Account age distribution is deliberately skewed: most accounts are
    established, a meaningful minority are brand-new (created within the
    last few days of the platform window) since account freshness is one
    of the genuine fraud signals available from existing fields.
    """
    n_total = config.N_ORGANIZERS + config.N_CUSTOMERS
    user_id = np.arange(1, n_total + 1)
    role = np.array(
        ["organizer"] * config.N_ORGANIZERS + ["customer"] * config.N_CUSTOMERS
    )

    # Account creation dates: long-tailed toward "older" accounts, with a
    # thin spike of very recent signups (day of / day before their first order).
    account_age_days_from_now = rng.gamma(shape=2.2, scale=140, size=n_total)
    account_age_days_from_now = np.clip(account_age_days_from_now, 0, 900)
    account_created_at = pd.Series(
        pd.to_datetime(config.PLATFORM_NOW) - pd.to_timedelta(account_age_days_from_now, unit="D")
    )
    # Clip so nobody is "created" before the platform itself conceptually existed
    lower_bound = pd.Timestamp(config.PLATFORM_START) - timedelta(days=730)
    account_created_at = account_created_at.clip(lower=lower_bound)

    is_verified = rng.random(n_total) < np.where(
        role == "organizer", 0.97, 0.82
    )
    is_active = rng.random(n_total) < 0.985

    df = pd.DataFrame(
        {
            "user_id": user_id,
            "role": role,
            "is_active": is_active,
            "is_verified": is_verified,
            "account_created_at": account_created_at,
        }
    )
    logger.info("Generated users table: %s", df.shape)
    return df


def generate_events(rng: np.random.Generator, users_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate the events table, each owned by a random organizer, matching
    app.models.Event.Event. `listed_at` (Event.created_at) is when tickets
    went on sale, always before start_datetime.
    """
    organizer_ids = users_df.loc[users_df["role"] == "organizer", "user_id"].to_numpy()

    event_id = np.arange(1, config.N_EVENTS + 1)
    organizer_id = rng.choice(organizer_ids, size=config.N_EVENTS)

    categories, cat_weights = zip(*[(c, 1.0) for c in config.EVENT_CATEGORIES])
    category = rng.choice(config.EVENT_CATEGORIES, size=config.N_EVENTS)

    city_country = [cc for cc, _ in config.CITY_COUNTRY_WEIGHTS]
    weights = np.array([w for _, w in config.CITY_COUNTRY_WEIGHTS])
    weights = weights / weights.sum()
    idx = rng.choice(len(city_country), size=config.N_EVENTS, p=weights)
    city = np.array([city_country[i][0] for i in idx])
    country = np.array([city_country[i][1] for i in idx])

    # Event start dates spread across (and a bit beyond) the platform window
    start_offsets = rng.integers(
        0, (config.PLATFORM_NOW - config.PLATFORM_START).days + 120, size=config.N_EVENTS
    )
    start_datetime = pd.to_datetime(config.PLATFORM_START) + pd.to_timedelta(
        start_offsets, unit="D"
    )
    start_datetime += pd.to_timedelta(rng.integers(8, 23, size=config.N_EVENTS), unit="h")
    duration_hours = rng.integers(2, 8, size=config.N_EVENTS)
    end_datetime = start_datetime + pd.to_timedelta(duration_hours, unit="h")

    # Tickets typically go on sale 15-120 days before the event
    lead_days = rng.integers(15, 120, size=config.N_EVENTS)
    listed_at = start_datetime - pd.to_timedelta(lead_days, unit="D")
    # Don't let a listing date predate the platform's own launch
    listed_at = pd.Series(listed_at).clip(lower=pd.Timestamp(config.PLATFORM_START)).values
    listed_at = pd.to_datetime(listed_at)

    # Capacity varies a lot by category (festivals/concerts >> workshops)
    base_capacity = rng.lognormal(mean=6.3, sigma=1.0, size=config.N_EVENTS)
    max_capacity = np.clip(base_capacity, 30, 20_000).astype(int)

    df = pd.DataFrame(
        {
            "event_id": event_id,
            "organizer_id": organizer_id,
            "category": category,
            "city": city,
            "country": country,
            "max_capacity": max_capacity,
            "listed_at": listed_at,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
        }
    )
    logger.info("Generated events table: %s", df.shape)
    return df


def generate_ticket_tiers(rng: np.random.Generator, events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate 1-4 ticket tiers per event, matching app.models.Ticket.TicketTier.
    Higher tiers (VIP/Platinum) are priced as a multiple of the base tier.
    """
    rows = []
    tier_id = 1
    for _, ev in events_df.iterrows():
        n_tiers = rng.choice([1, 2, 3, 4], p=[0.30, 0.35, 0.25, 0.10])
        names = rng.choice(config.TIER_NAMES, size=n_tiers, replace=False)

        base_price = float(np.clip(rng.lognormal(mean=3.6, sigma=0.7), 8, 900))
        remaining_capacity = int(ev["max_capacity"])
        # Split capacity across tiers unevenly (general admission gets the bulk)
        splits = rng.dirichlet(np.ones(n_tiers) * (2.5 if n_tiers > 1 else 1))
        seats_per_tier = np.maximum(5, (splits * remaining_capacity).astype(int))

        for i, name in enumerate(names):
            multiplier = {
                "Early Bird": 0.75, "General Admission": 1.0, "Standard": 1.0,
                "Balcony": 0.85, "VIP": 2.4, "Platinum": 3.8,
            }.get(name, 1.0)
            price = round(base_price * multiplier * rng.uniform(0.92, 1.08), 2)
            rows.append(
                {
                    "tier_id": tier_id,
                    "event_id": ev["event_id"],
                    "category_name": name,
                    "price": price,
                    "currency": config.CURRENCY,
                    "total_seats": int(seats_per_tier[i]),
                }
            )
            tier_id += 1

    df = pd.DataFrame(rows)
    logger.info("Generated ticket_tiers table: %s", df.shape)
    return df
