"""
Phase 14 — Production prediction pipeline.

This is the one object the FastAPI app needs to import. It wraps schema
validation, feature alignment, preprocessing, and the trained model behind
two methods:

    prediction  = fraud_pipeline.predict(input_data)
    probability = fraud_pipeline.predict_proba(input_data)

`input_data` may be a dict (single order) or a DataFrame (batch), and only
needs to contain schema_contract.CORE_FEATURES — every OPTIONAL_FEATURES
column is filled with its documented safe default automatically. No
preprocessing, imputation, or encoding is the caller's responsibility.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import schema_contract as sc

logger = logging.getLogger("training_pipeline.inference")


class FraudDetectionPipeline:
    """Thin, serializable wrapper around a fitted sklearn/imblearn Pipeline."""

    def __init__(self, fitted_pipeline, model_name: str, decision_threshold: float = 0.5,
                 metadata: dict | None = None):
        self.fitted_pipeline = fitted_pipeline
        self.model_name = model_name
        self.decision_threshold = decision_threshold
        self.metadata = metadata or {}

    def _to_dataframe(self, input_data) -> pd.DataFrame:
        if isinstance(input_data, pd.DataFrame):
            return input_data.copy()
        if isinstance(input_data, dict):
            return pd.DataFrame([input_data])
        if isinstance(input_data, list):
            return pd.DataFrame(input_data)
        raise TypeError(f"Unsupported input_data type: {type(input_data)}. Expected dict, list[dict], or DataFrame.")

    def validate_schema(self, df: pd.DataFrame) -> None:
        missing_core = [c for c in sc.CORE_FEATURES if c not in df.columns]
        if missing_core:
            raise ValueError(
                f"Cannot score this input — missing required field(s): {missing_core}. "
                f"These must be supplied by the application (they're all derivable from "
                f"existing User/Event/TicketTier/Order data with no schema changes)."
            )

    def predict_proba(self, input_data) -> np.ndarray:
        df = self._to_dataframe(input_data)
        self.validate_schema(df)
        return self.fitted_pipeline.predict_proba(df)[:, 1]

    def predict(self, input_data, threshold: float | None = None) -> np.ndarray:
        proba = self.predict_proba(input_data)
        t = threshold if threshold is not None else self.decision_threshold
        return (proba >= t).astype(int)

    def explain_single(self, input_data) -> dict:
        """
        Lightweight, dependency-free explanation for a single prediction:
        which optional signals were actually available vs defaulted, and
        the resulting score. For full SHAP explanations use
        evaluation.compute_shap_values on a batch instead (heavier, more
        precise, not meant for a single hot-path prediction call).
        """
        df = self._to_dataframe(input_data)
        self.validate_schema(df)
        row = df.iloc[0]
        used_optional = [c for c in sc.OPTIONAL_FEATURES if c in df.columns and pd.notna(row.get(c))]
        defaulted_optional = [c for c in sc.OPTIONAL_FEATURES if c not in df.columns or pd.isna(row.get(c))]
        proba = float(self.predict_proba(df)[0])
        return {
            "fraud_probability": proba,
            "prediction": int(proba >= self.decision_threshold),
            "optional_signals_used": used_optional,
            "optional_signals_defaulted": defaulted_optional,
        }

    def save(self, path: Path) -> None:
        import joblib
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Saved production pipeline to %s", path)

    @classmethod
    def load(cls, path: Path) -> "FraudDetectionPipeline":
        import joblib
        return joblib.load(path)
