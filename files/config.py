"""
Configuration and reference data for the Tixora synthetic dataset generator.

Kept separate from the generation logic so paths, volumes, and reference
lists can be tuned without touching the generation algorithms.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

for _dir in (DATA_DIR, LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Reproducibility & volume
# --------------------------------------------------------------------------- #
RANDOM_STATE = 42

N_ORGANIZERS = 130
N_CUSTOMERS = 6_000
N_EVENTS = 480
TARGET_N_ORDERS = 55_000

# Platform activity window (orders are generated inside this window)
PLATFORM_START = datetime(2025, 9, 1)
PLATFORM_NOW = datetime(2026, 7, 24)

# Approximate overall fraud prevalence (industry-realistic for ticketing: 2-6%)
TARGET_FRAUD_RATE = 0.045

# --------------------------------------------------------------------------- #
# Reference data (mirrors realistic values an events platform would see)
# --------------------------------------------------------------------------- #
EVENT_CATEGORIES = [
    "Concert", "Sports", "Theater", "Conference", "Festival",
    "Comedy", "Workshop", "Exhibition", "Nightlife", "Family",
]

# (city, country) with weights — a handful of "home market" cities dominate,
# a long tail of others, which is realistic for a regional ticketing platform.
CITY_COUNTRY_WEIGHTS = [
    (("Lahore", "Pakistan"), 0.22),
    (("Karachi", "Pakistan"), 0.16),
    (("Islamabad", "Pakistan"), 0.12),
    (("Dubai", "UAE"), 0.09),
    (("London", "UK"), 0.07),
    (("New York", "USA"), 0.06),
    (("Toronto", "Canada"), 0.05),
    (("Riyadh", "Saudi Arabia"), 0.05),
    (("Doha", "Qatar"), 0.04),
    (("Manchester", "UK"), 0.03),
    (("Los Angeles", "USA"), 0.03),
    (("Istanbul", "Turkey"), 0.03),
    (("Singapore", "Singapore"), 0.025),
    (("Sydney", "Australia"), 0.025),
]

TIER_NAMES = ["Early Bird", "General Admission", "VIP", "Platinum", "Standard", "Balcony"]

CURRENCY = "USD"
