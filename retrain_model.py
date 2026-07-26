"""
Retrain the XGBoost fraud detection model from CSV data.

This script replicates the exact training pipeline from files/merge.py,
files/feature_engineering.py, files/preprocessing.py, and files/training.py,
producing a Pipeline object identical in structure to the original best_model.pkl.

Saves with pickle.dump() so pickle.load() works in model_loader.py.
"""
from __future__ import annotations

import logging
import pickle
import sys
import time
import types
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("retrain")

RANDOM_STATE = 42
DATA_DIR = Path("files")
OUT_DIR = Path("app/services/fraud_detection")

# ────────────────────────────────────────────────────────────────────
# Feature lists (from schema_contract.py)
# ────────────────────────────────────────────────────────────────────
CORE_NUMERIC_FEATURES = [
    "quantity", "total_price", "price_per_ticket", "price_deviation_from_listed",
    "account_age_days", "purchases_last_1h", "purchases_last_24h", "purchases_last_7d",
    "spend_last_24h", "spend_last_7d", "distinct_events_last_24h",
    "time_since_last_order_hours", "user_lifetime_order_count",
    "user_historical_refund_rate", "user_historical_paid_rate",
    "purchase_hour", "purchase_weekday", "purchase_month",
    "days_until_event", "hours_since_tier_listed",
    "quantity_share_of_tier_capacity", "event_popularity_ratio",
    "organizer_historical_refund_rate",
]
CORE_BOOLEAN_FEATURES = ["is_verified", "is_active", "is_first_order", "is_weekend", "is_late_night"]
CORE_CATEGORICAL_FEATURES = ["event_category"]
CORE_FEATURES = CORE_NUMERIC_FEATURES + CORE_BOOLEAN_FEATURES + CORE_CATEGORICAL_FEATURES

OPTIONAL_NUMERIC_DEFAULTS = {
    "failed_payments": 0.0, "payment_attempts": 0.0,
    "purchases_same_device_24h": 0.0, "purchases_same_ip_24h": 0.0,
    "purchases_same_card_24h": 0.0, "unique_devices_per_user": 0.0,
    "unique_cards_per_device": 0.0,
}
OPTIONAL_BOOLEAN_DEFAULTS = {
    "vpn_detected": 0.0, "proxy_detected": 0.0, "datacenter_ip": 0.0,
    "phone_verified": 0.0, "ip_event_country_mismatch": 0.0,
}
OPTIONAL_CATEGORICAL_DEFAULTS = {
    "device_type": "Unknown", "browser": "Unknown", "operating_system": "Unknown",
    "ip_country": "Unknown", "ip_city": "Unknown",
}
OPTIONAL_DEFAULTS = {**OPTIONAL_NUMERIC_DEFAULTS, **OPTIONAL_BOOLEAN_DEFAULTS, **OPTIONAL_CATEGORICAL_DEFAULTS}
OPTIONAL_NUMERIC_FEATURES = list(OPTIONAL_NUMERIC_DEFAULTS) + list(OPTIONAL_BOOLEAN_DEFAULTS)
OPTIONAL_CATEGORICAL_FEATURES = list(OPTIONAL_CATEGORICAL_DEFAULTS)
OPTIONAL_FEATURES = OPTIONAL_NUMERIC_FEATURES + OPTIONAL_CATEGORICAL_FEATURES

LEAKAGE_COLUMNS = ["status", "has_qr_code", "fraud_type", "is_fraud"]
IDENTIFIER_COLUMNS = [
    "order_id", "user_id", "event_id", "tier_id",
    "device_id", "ip_address", "card_fingerprint", "user_agent", "created_at",
]


# ────────────────────────────────────────────────────────────────────
# Schema alignment (from schema_contract.py)
# ────────────────────────────────────────────────────────────────────
def align_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = df[col].astype(object)
    for col, default in OPTIONAL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
        else:
            if isinstance(df[col].dtype, pd.CategoricalDtype):
                df[col] = df[col].astype(object)
            df[col] = df[col].fillna(default)
    return df[CORE_FEATURES + OPTIONAL_FEATURES]


# ────────────────────────────────────────────────────────────────────
# Preprocessing pipeline classes (from preprocessing.py)
# Registered under pipeline.preprocessing so pickle records the correct
# module path, matching the shim in model_loader.py.
# ────────────────────────────────────────────────────────────────────
_pipeline_pkg = types.ModuleType("pipeline")
_pipeline_pkg.__path__ = []
_pipeline_pkg.__package__ = "pipeline"
sys.modules["pipeline"] = _pipeline_pkg

_pipeline_prep = types.ModuleType("pipeline.preprocessing")
_pipeline_prep.__package__ = "pipeline"
sys.modules["pipeline.preprocessing"] = _pipeline_prep


class SchemaAlignerTransformer(BaseEstimator, TransformerMixin):
    __module__ = "pipeline.preprocessing"

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return align_to_schema(X)

    def get_feature_names_out(self, input_features=None):
        return np.array(CORE_FEATURES + OPTIONAL_FEATURES)


class _CleaningTransformer(BaseEstimator, TransformerMixin):
    __module__ = "pipeline.preprocessing"

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X[numeric_cols] = X[numeric_cols].replace([np.inf, -np.inf], np.nan)
        non_negative_cols = [c for c in numeric_cols if c not in ("price_deviation_from_listed",)]
        for col in non_negative_cols:
            X.loc[X[col] < 0, col] = np.nan
        for col in X.select_dtypes(include=["float64"]).columns:
            X[col] = pd.to_numeric(X[col], downcast="float")
        return X


_pipeline_prep.SchemaAlignerTransformer = SchemaAlignerTransformer
_pipeline_prep._CleaningTransformer = _CleaningTransformer


def build_preprocessing_pipeline() -> Pipeline:
    core_numeric = CORE_NUMERIC_FEATURES + CORE_BOOLEAN_FEATURES
    optional_numeric = OPTIONAL_NUMERIC_FEATURES
    core_categorical = CORE_CATEGORICAL_FEATURES
    optional_categorical = OPTIONAL_CATEGORICAL_FEATURES

    core_numeric_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    optional_numeric_pipe = Pipeline([("impute", SimpleImputer(strategy="constant", fill_value=0.0)), ("scale", StandardScaler())])
    core_categorical_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore"))])
    optional_categorical_pipe = Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="Unknown")), ("encode", OneHotEncoder(handle_unknown="ignore"))])

    column_transformer = ColumnTransformer(
        transformers=[
            ("core_num", core_numeric_pipe, core_numeric),
            ("opt_num", optional_numeric_pipe, optional_numeric),
            ("core_cat", core_categorical_pipe, core_categorical),
            ("opt_cat", optional_categorical_pipe, optional_categorical),
        ],
        remainder="drop",
    )

    return Pipeline([
        ("schema_align", SchemaAlignerTransformer()),
        ("clean", _CleaningTransformer()),
        ("preprocess", column_transformer),
    ])


# ────────────────────────────────────────────────────────────────────
# Rolling / expanding helpers (from feature_engineering.py)
# ────────────────────────────────────────────────────────────────────
def _rolling_prior_count_sum(df, key_col, time_col, window, value_col=None):
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


def _expanding_prior_rate(df, key_col, time_col, flag_col):
    valid_sorted = df.sort_values([key_col, time_col])
    grp = valid_sorted.groupby(key_col, observed=True)[flag_col]
    cum_sum = grp.cumsum() - valid_sorted[flag_col]
    cum_count = grp.cumcount()
    prior_rate = (cum_sum / cum_count.replace(0, np.nan)).fillna(0.0)
    return prior_rate.reindex(df.index)


def _first_occurrence_running_distinct(df, group_col, item_col):
    has_item = df[item_col].notna()
    is_new = (~df.duplicated(subset=[group_col, item_col], keep="first")) & has_item
    cumulative_incl_self = is_new.groupby(df[group_col], observed=True).cumsum()
    return cumulative_incl_self - is_new.astype(int)


# ────────────────────────────────────────────────────────────────────
# Merge (from merge.py)
# ────────────────────────────────────────────────────────────────────
def load_and_merge(data_dir: Path) -> pd.DataFrame:
    logger.info("Loading raw CSVs from %s ...", data_dir)
    users = pd.read_csv(data_dir / "users.csv", parse_dates=["account_created_at"])
    events = pd.read_csv(data_dir / "events.csv", parse_dates=["listed_at", "start_datetime", "end_datetime"])
    tiers = pd.read_csv(data_dir / "ticket_tiers.csv")
    orders = pd.read_csv(data_dir / "orders.csv", parse_dates=["created_at"])
    enrichment = pd.read_csv(data_dir / "order_enrichment.csv")

    for name, df in [("users", users), ("events", events), ("tiers", tiers), ("orders", orders), ("enrichment", enrichment)]:
        logger.info("  %s: %d rows, %d cols", name, *df.shape)

    # Drop order-level placeholder columns that overlap with enrichment
    orders = orders.drop(columns=["ip_address", "user_agent", "device_id"], errors="ignore")

    df = orders.merge(
        tiers.rename(columns={"price": "tier_listed_price"}),
        on="tier_id", how="left", validate="many_to_one", suffixes=("", "_tier"),
    )
    if "event_id_tier" in df.columns:
        df = df.drop(columns=["event_id_tier"])

    df = df.merge(
        events.rename(columns={"category": "event_category"}),
        on="event_id", how="left", validate="many_to_one", suffixes=("", "_event"),
    )
    df = df.merge(users, on="user_id", how="left", validate="many_to_one", suffixes=("", "_user"))
    df = df.merge(enrichment, on="order_id", how="left", validate="one_to_one")

    logger.info("Merged dataset: %d rows, %d cols", *df.shape)
    return df


# ────────────────────────────────────────────────────────────────────
# Feature engineering (from feature_engineering.py)
# ────────────────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.sort_values(["user_id", "created_at"]).reset_index(drop=True)
    df["_row_id"] = np.arange(len(df))

    # ── Core features ──
    df["price_per_ticket"] = df["total_price"] / df["quantity"].replace(0, np.nan)
    df["price_deviation_from_listed"] = (df["price_per_ticket"] - df["tier_listed_price"]).fillna(0.0)
    df["account_age_days"] = (df["created_at"] - df["account_created_at"]).dt.total_seconds() / 86400
    df["purchase_hour"] = df["created_at"].dt.hour
    df["purchase_weekday"] = df["created_at"].dt.dayofweek
    df["purchase_month"] = df["created_at"].dt.month
    df["is_weekend"] = df["purchase_weekday"].isin([5, 6]).astype(int)
    df["is_late_night"] = df["purchase_hour"].between(0, 4).astype(int)
    df["days_until_event"] = (df["start_datetime"] - df["created_at"]).dt.total_seconds() / 86400
    df["hours_since_tier_listed"] = (df["created_at"] - df["listed_at"]).dt.total_seconds() / 3600
    df["quantity_share_of_tier_capacity"] = df["quantity"] / df["total_seats"].replace(0, np.nan)

    is_paid = (df["status"] == "paid").astype(int)
    is_refunded = (df["status"] == "refunded").astype(int)

    # ── Rolling windows ──
    r1h = _rolling_prior_count_sum(df, "user_id", "created_at", "1h")
    r24h = _rolling_prior_count_sum(df, "user_id", "created_at", "24h", value_col="total_price")
    r7d = _rolling_prior_count_sum(df, "user_id", "created_at", "7D")
    r7d_spend = _rolling_prior_count_sum(df, "user_id", "created_at", "7D", value_col="total_price")

    df["purchases_last_1h"] = r1h["count_prior"].clip(lower=0).fillna(0).to_numpy()
    df["purchases_last_24h"] = r24h["count_prior"].clip(lower=0).fillna(0).to_numpy()
    df["spend_last_24h"] = r24h["sum_prior"].clip(lower=0).fillna(0).to_numpy()
    df["purchases_last_7d"] = r7d["count_prior"].clip(lower=0).fillna(0).to_numpy()
    df["spend_last_7d"] = r7d_spend["sum_prior"].clip(lower=0).fillna(0).to_numpy()
    df["distinct_events_last_24h"] = df["purchases_last_24h"]

    # ── User history ──
    grp = df.groupby("user_id", observed=True)
    df["time_since_last_order_hours"] = (
        (df["created_at"] - grp["created_at"].shift(1)).dt.total_seconds() / 3600
    ).fillna(999.0).clip(lower=0)
    df["user_lifetime_order_count"] = grp.cumcount()
    df["is_first_order"] = (df["user_lifetime_order_count"] == 0).astype(int)

    df["_is_paid_tmp"] = is_paid.to_numpy()
    df["_is_refunded_tmp"] = is_refunded.to_numpy()
    df["user_historical_paid_rate"] = _expanding_prior_rate(df, "user_id", "created_at", "_is_paid_tmp")
    df["user_historical_refund_rate"] = _expanding_prior_rate(df, "user_id", "created_at", "_is_refunded_tmp")

    # ── Event popularity ──
    event_qty = _rolling_prior_count_sum(
        df.assign(_v=df["quantity"]), "event_id", "created_at", "3650D", value_col="quantity"
    )
    df["event_popularity_ratio"] = (
        (event_qty["sum_prior"].clip(lower=0) / df["max_capacity"].replace(0, np.nan)).fillna(0.0).to_numpy()
    )

    # ── Organizer refund rate ──
    df["organizer_historical_refund_rate"] = _expanding_prior_rate(
        df, "organizer_id", "created_at", "_is_refunded_tmp"
    )

    # ── Optional enrichment features ──
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

    # ── Extract label and build feature matrix ──
    y = df["is_fraud"].astype(int).reset_index(drop=True)
    keep_cols = CORE_FEATURES + OPTIONAL_FEATURES
    X = df[keep_cols].reset_index(drop=True)

    df = df.drop(columns=["_is_paid_tmp", "_is_refunded_tmp", "_row_id"], errors="ignore")

    logger.info("Feature matrix: %d rows, %d features", X.shape[0], X.shape[1])
    return X, y


# ────────────────────────────────────────────────────────────────────
# Main training routine
# ────────────────────────────────────────────────────────────────────
def main():
    # 1. Load and merge
    master_df = load_and_merge(DATA_DIR)

    # 2. Feature engineering
    X, y = engineer_features(master_df)
    logger.info("Fraud rate: %.4f%%", 100 * y.mean())

    # 3. Stratified split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE)
    logger.info("Train: %d (%.2f%% fraud), Val: %d (%.2f%% fraud), Test: %d (%.2f%% fraud)",
                len(X_train), 100 * y_train.mean(), len(X_val), 100 * y_val.mean(), len(X_test), 100 * y_test.mean())

    # 4. Build pipeline (matches training.py build_full_pipeline)
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    logger.info("scale_pos_weight: %.2f", scale_pos_weight)

    full_pipeline = Pipeline([
        ("preprocess", build_preprocessing_pipeline()),
        ("classifier", XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.02,
            subsample=0.85, colsample_bytree=0.85,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1,
        )),
    ])

    # 5. Train
    logger.info("Training XGBoost...")
    t0 = time.time()
    full_pipeline.fit(X_train, y_train)
    train_time = time.time() - t0
    logger.info("Training completed in %.1fs", train_time)

    # 6. Evaluate
    y_prob = full_pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "pr_auc": average_precision_score(y_test, y_prob),
    }
    cm = confusion_matrix(y_test, y_pred)
    logger.info("Test metrics @ threshold=0.5:")
    for k, v in metrics.items():
        logger.info("  %s: %.4f", k, v)
    logger.info("  confusion: %s", cm.tolist())

    # 7. Save with pickle.dump() — this is what model_loader.py uses
    out_path = OUT_DIR / "best_model.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(full_pipeline, f)
    logger.info("Saved pipeline to %s (%d bytes)", out_path, out_path.stat().st_size)

    # 8. Verify both load methods work
    with open(out_path, "rb") as f:
        m1 = pickle.load(f)
    logger.info("pickle.load() OK — type=%s", type(m1).__name__)

    import joblib
    m2 = joblib.load(out_path)
    logger.info("joblib.load() OK — type=%s", type(m2).__name__)

    # Quick round-trip prediction check
    pred_pickle = m1.predict(X_test.iloc[:5])
    pred_joblib = m2.predict(X_test.iloc[:5])
    logger.info("Predictions match: %s", (pred_pickle == pred_joblib).all())

    logger.info("DONE — best_model.pkl is ready for both pickle.load() and joblib.load()")


if __name__ == "__main__":
    main()
