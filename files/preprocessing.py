"""
Phase 5 — Data cleaning (vectorized) and
Phase 7 — Preprocessing pipeline.

Key design decision: OPTIONAL features are defaulted to a fixed, documented
constant (0 / "Unknown" / False) via `SchemaAlignerTransformer`, applied
IDENTICALLY at training time and at inference time. This is deliberate:
using a statistically-fitted imputer (e.g. median/mode learned from training
data) for a column that's *usually absent in production* would mean
training-time imputation and inference-time imputation could diverge
subtly — a real train/serve skew risk. A fixed domain default ("no VPN
signal available" -> treat as 0) is simpler and consistent everywhere.

CORE features get a conventional statistical imputer as a defensive
safety net only — they should never actually be missing, since they're
always computable from data the application already has.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..app.services.fraud_detection import schema_contract as sc

logger = logging.getLogger("training_pipeline.preprocessing")


class SchemaAlignerTransformer(BaseEstimator, TransformerMixin):
    """
    Sklearn-compatible wrapper around schema_contract.align_to_schema.
    Stateless: fit() is a no-op. Guarantees the output always has every
    CORE_FEATURES + OPTIONAL_FEATURES column, in a fixed order, regardless
    of which optional columns were present in the input.
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        return sc.align_to_schema(X)

    def get_feature_names_out(self, input_features=None):
        return np.array(sc.CORE_FEATURES + sc.OPTIONAL_FEATURES)


def clean_dataframe(X: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized data-cleaning pass (Phase 5): duplicate rows, invalid
    numeric values (inf, absurd negatives), and dtype optimization.
    No row-wise Python loops.
    """
    X = X.copy()
    n_before = len(X)
    X = X.drop_duplicates()
    if len(X) != n_before:
        logger.info("Dropped %s exact duplicate rows during cleaning", n_before - len(X))

    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].replace([np.inf, -np.inf], np.nan)
    # Physically-impossible negative values (shouldn't occur, but a real
    # pipeline must not trust upstream data blindly)
    non_negative_cols = [c for c in numeric_cols if c not in ("price_deviation_from_listed",)]
    for col in non_negative_cols:
        X.loc[X[col] < 0, col] = np.nan

    for col in X.select_dtypes(include=["float64"]).columns:
        X[col] = pd.to_numeric(X[col], downcast="float")
    return X


def build_preprocessing_pipeline() -> Pipeline:
    """
    Full Phase 5+7 pipeline: schema alignment -> cleaning-safe imputation ->
    encoding -> scaling. This Pipeline is the first half of every model's
    full pipeline (see training.py), and is also reused directly inside the
    production inference wrapper (Phase 14) so training and serving never
    diverge.
    """
    core_numeric = sc.CORE_NUMERIC_FEATURES + sc.CORE_BOOLEAN_FEATURES
    optional_numeric = sc.OPTIONAL_NUMERIC_FEATURES
    core_categorical = sc.CORE_CATEGORICAL_FEATURES
    optional_categorical = sc.OPTIONAL_CATEGORICAL_FEATURES

    core_numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    optional_numeric_pipe = Pipeline([
        # Safety net only — SchemaAlignerTransformer already substitutes 0
        # for genuinely absent optional data before this ever runs.
        ("impute", SimpleImputer(strategy="constant", fill_value=0.0)),
        ("scale", StandardScaler()),
    ])
    core_categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    optional_categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])

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


class _CleaningTransformer(BaseEstimator, TransformerMixin):
    """Wraps clean_dataframe() as a pipeline step."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return clean_dataframe(X)
