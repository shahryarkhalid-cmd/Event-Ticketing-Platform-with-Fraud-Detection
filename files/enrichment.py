"""
Optional enrichment signal generator.

IMPORTANT: everything generated here does NOT exist in the live application
schema today (no device/IP/card capture, no Stripe payment-attempt logging
into `Order`, no phone verification field on `User`). This module exists
only to give the *training* pipeline realistic signal to learn from, on the
explicit understanding that:

  1. None of these columns are required at inference time.
  2. A meaningful fraction of TRAINING rows are also generated with this
     data entirely absent, so the model is trained under the same
     missingness it will see in production (where 100% of rows lack it
     until the app is upgraded to capture it).
  3. See pipeline/schema_contract.py for how "optional" is enforced
     end-to-end (safe defaults, no hard requirement, graceful fallback).

Correlated with `fraud_type` for realistic (not random) signal, but with
deliberate overlap/noise so no single optional feature is independently
decisive — consistent with the rest of the dataset design.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger("dataset_generator.enrichment")

DEVICE_TYPES = ["mobile", "desktop", "tablet"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Samsung Internet", "Other"]
OPERATING_SYSTEMS = {
    "mobile": ["iOS", "Android"],
    "desktop": ["Windows", "macOS", "Linux"],
    "tablet": ["iOS", "Android", "Windows"],
}

# Fraud archetypes that skew toward "risky" network/device signatures.
HIGH_RISK_TYPES = {"bot_card_testing", "new_account_high_value", "scalping_bulk"}
MODERATE_RISK_TYPES = {"account_takeover", "refund_abuse"}


def _make_user_agent(rng, device_type: str, os_name: str, browser: str) -> str:
    return f"{device_type}/{os_name}/{browser}"


def generate_enrichment(rng: np.random.Generator, orders: pd.DataFrame) -> pd.DataFrame:
    """
    Generate one enrichment row per order_id. Returns a DataFrame keyed on
    `order_id` so it's a clean left-join onto the core orders table.

    Design:
      - ~16% of ALL orders (any fraud_type) get NO enrichment at all
        (simulates the current 100%-missing reality, at a lower rate here
        so the model still has enough signal to learn from during training).
      - bot_card_testing bursts reuse a small pool of device_id/ip_address
        values across many different user_ids (bot farm signature).
      - risk flags (vpn/proxy/datacenter, failed payments, low phone
        verification) are sampled with elevated-but-overlapping
        probabilities for fraud archetypes, never as hard 0/1 rules.
    """
    n = len(orders)
    has_enrichment = rng.random(n) >= 0.16

    device_type = rng.choice(DEVICE_TYPES, size=n, p=[0.62, 0.34, 0.04])
    os_name = np.array([rng.choice(OPERATING_SYSTEMS[dt]) for dt in device_type])
    browser = rng.choice(BROWSERS, size=n, p=[0.52, 0.22, 0.12, 0.09, 0.03, 0.02])
    user_agent = np.array(
        [_make_user_agent(rng, dt, os_, b) for dt, os_, b in zip(device_type, os_name, browser)]
    )

    fraud_type = orders["fraud_type"].to_numpy()
    is_high_risk = np.isin(fraud_type, list(HIGH_RISK_TYPES))
    is_moderate_risk = np.isin(fraud_type, list(MODERATE_RISK_TYPES))

    # --- device_id: mostly stable per user, but bot bursts share a small device pool ---
    device_id = np.array([f"dev_{rng.integers(100_000, 999_999)}" for _ in range(n)])
    bot_burst_mask = fraud_type == "bot_card_testing"
    if bot_burst_mask.any():
        # Reuse a handful of shared "bot" device ids across all bot_card_testing rows
        shared_devices = np.array([f"dev_bot_{i}" for i in range(6)])
        device_id[bot_burst_mask] = rng.choice(shared_devices, size=bot_burst_mask.sum())

    # A minority of returning legit customers reuse the same 1-2 devices across their own orders
    per_user_device = orders.groupby("user_id")["user_id"].transform("count") > 1
    legit_repeat_mask = (~is_high_risk) & (~is_moderate_risk) & per_user_device.to_numpy() & (rng.random(n) < 0.7)
    if legit_repeat_mask.any():
        stable_lookup = {
            uid: f"dev_{rng.integers(100_000, 999_999)}" for uid in orders.loc[legit_repeat_mask, "user_id"].unique()
        }
        device_id[legit_repeat_mask] = orders.loc[legit_repeat_mask, "user_id"].map(stable_lookup).to_numpy()

    # --- ip_address: similarly, bot bursts share a small IP pool ---
    ip_address = np.array(
        [f"{rng.integers(1,224)}.{rng.integers(0,256)}.{rng.integers(0,256)}.{rng.integers(1,255)}" for _ in range(n)]
    )
    if bot_burst_mask.any():
        shared_ips = np.array(
            [f"{rng.integers(1,224)}.{rng.integers(0,256)}.{rng.integers(0,256)}.{rng.integers(1,255)}" for _ in range(5)]
        )
        ip_address[bot_burst_mask] = rng.choice(shared_ips, size=bot_burst_mask.sum())

    # --- card_fingerprint: forward-looking, hypothetical future Stripe-webhook field ---
    card_fingerprint = np.array([f"card_{rng.integers(10_000, 99_999)}" for _ in range(n)])
    if bot_burst_mask.any():
        shared_cards = np.array([f"card_test_{i}" for i in range(4)])
        card_fingerprint[bot_burst_mask] = rng.choice(shared_cards, size=bot_burst_mask.sum())

    # --- risk flags: elevated-but-overlapping probabilities ---
    base_vpn_p = 0.04
    vpn_p = np.where(is_high_risk, 0.38, np.where(is_moderate_risk, 0.15, base_vpn_p))
    vpn_detected = rng.random(n) < vpn_p

    base_proxy_p = 0.03
    proxy_p = np.where(is_high_risk, 0.30, np.where(is_moderate_risk, 0.10, base_proxy_p))
    proxy_detected = rng.random(n) < proxy_p

    base_dc_p = 0.02
    dc_p = np.where(fraud_type == "bot_card_testing", 0.55, np.where(is_high_risk, 0.20, base_dc_p))
    datacenter_ip = rng.random(n) < dc_p

    # --- ip_country / ip_city: mostly the platform's usual markets; fraud
    # archetypes have an elevated (not exclusive) chance of an unusual country ---
    from . import config
    home_countries = [cc[1] for cc, _ in config.CITY_COUNTRY_WEIGHTS]
    home_weights = np.array([w for _, w in config.CITY_COUNTRY_WEIGHTS])
    home_weights = home_weights / home_weights.sum()

    unusual_countries = ["Nigeria", "Vietnam", "Romania", "Indonesia", "Russia", "Brazil"]

    unusual_p = np.where(is_high_risk, 0.32, np.where(is_moderate_risk, 0.10, 0.02))
    use_unusual = rng.random(n) < unusual_p
    idx = rng.choice(len(home_countries), size=n, p=home_weights)
    ip_country = np.array(home_countries)[idx]
    if use_unusual.any():
        ip_country[use_unusual] = rng.choice(unusual_countries, size=use_unusual.sum())
    city_by_country = {cc[1]: cc[0] for cc, _ in config.CITY_COUNTRY_WEIGHTS}
    ip_city = np.array([city_by_country.get(c, "Unknown") for c in ip_country])

    # --- payments: fraud archetypes see more failed attempts BEFORE the final
    # charge — this reflects real-time checkout telemetry (card declines during
    # this session), never the order's eventual settlement status, which is
    # not known at scoring time and is excluded from features entirely
    # (see pipeline/feature_engineering.py leakage notes). ---
    failed_p = np.where(fraud_type == "bot_card_testing", 0.55,
                np.where(fraud_type == "new_account_high_value", 0.30,
                np.where(is_moderate_risk, 0.12, 0.04)))
    failed_payments = rng.binomial(3, failed_p)
    payment_attempts = failed_payments + 1  # the attempt that produced this Order row

    # --- phone verification: lower for unverified/new/fraud-leaning accounts ---
    phone_p = np.where(is_high_risk, 0.35, np.where(is_moderate_risk, 0.55, 0.78))
    phone_verified = rng.random(n) < phone_p

    df = pd.DataFrame(
        {
            "order_id": orders["order_id"].to_numpy(),
            "device_id": device_id,
            "device_type": device_type,
            "browser": browser,
            "operating_system": os_name,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "ip_country": ip_country,
            "ip_city": ip_city,
            "vpn_detected": vpn_detected.astype(float),
            "proxy_detected": proxy_detected.astype(float),
            "datacenter_ip": datacenter_ip.astype(float),
            "card_fingerprint": card_fingerprint,
            "failed_payments": failed_payments.astype(float),
            "payment_attempts": payment_attempts.astype(float),
            "phone_verified": phone_verified.astype(float),
        }
    )

    # Blank out enrichment entirely for rows without it (simulates real missingness)
    enrichment_cols = [c for c in df.columns if c != "order_id"]
    df.loc[~has_enrichment, enrichment_cols] = np.nan

    logger.info(
        "Generated enrichment for %s / %s orders (%.1f%% missing by design)",
        int(has_enrichment.sum()), n, 100 * (1 - has_enrichment.mean()),
    )
    return df
