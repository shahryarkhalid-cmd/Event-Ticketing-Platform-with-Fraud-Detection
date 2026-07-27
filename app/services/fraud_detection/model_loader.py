"""Lazy-loading service for ML model artifacts.

Loads the trained model and preprocessing objects from pickle files
on first access, then caches them in memory for the process lifetime.

To swap the model:
  1. Train a new model and save it as pickle.
  2. Update the paths in FraudDetectionConfig (env vars or config.py).
  3. Restart the application — this module will load the new artifacts.

The loader is intentionally framework-agnostic: it works with any
scikit-learn-compatible estimator, XGBoost, LightGBM, or custom class
that exposes ``predict`` and ``predict_proba``.
"""

from __future__ import annotations

import logging
import pickle
import sys
import types
from pathlib import Path
from threading import Lock
from typing import Any, Tuple

import joblib

from .config import fraud_config

logger = logging.getLogger(__name__)

# Module-level cache (process singleton)
_model: Any = None
_load_lock = Lock()
_loaded = False


def _ensure_pipeline_shim() -> None:
    """Create in-memory ``pipeline.preprocessing`` shim so that pickles
    saved during training (which reference ``pipeline.preprocessing``
    module classes) can be deserialized at inference time.

    This is the minimum compatibility layer needed — it provides the
    exact same class signatures that were pickled during training.
    """
    if "pipeline" in sys.modules and "pipeline.preprocessing" in sys.modules:
        return

    import numpy as np
    import pandas as pd
    from sklearn.base import BaseEstimator, TransformerMixin

    from . import schema_contract as sc

    class SchemaAlignerTransformer(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            return sc.align_to_schema(X)

        def get_feature_names_out(self, input_features=None):
            return np.array(sc.CORE_FEATURES + sc.OPTIONAL_FEATURES)

    class _CleaningTransformer(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            X = X.copy()
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            X[numeric_cols] = X[numeric_cols].replace([np.inf, -np.inf], np.nan)
            non_negative_cols = [
                c for c in numeric_cols
                if c not in ("price_deviation_from_listed",)
            ]
            for col in non_negative_cols:
                X.loc[X[col] < 0, col] = np.nan
            for col in X.select_dtypes(include=["float64"]).columns:
                X[col] = pd.to_numeric(X[col], downcast="float")
            return X

    pipeline_pkg = types.ModuleType("pipeline")
    pipeline_pkg.__path__ = []
    pipeline_pkg.__package__ = "pipeline"
    sys.modules["pipeline"] = pipeline_pkg

    pipeline_prep = types.ModuleType("pipeline.preprocessing")
    pipeline_prep.__package__ = "pipeline"
    pipeline_prep.SchemaAlignerTransformer = SchemaAlignerTransformer
    pipeline_prep._CleaningTransformer = _CleaningTransformer
    sys.modules["pipeline.preprocessing"] = pipeline_prep

    logger.debug("Created pipeline.preprocessing compatibility shim")


def _load_pickle(path: str) -> Any:
    """Deserialize a pickle/joblib file and return the object.

    Tries joblib.load() first (handles numpy arrays, sklearn pipelines,
    and XGBoost models reliably), then falls back to pickle.load().
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    try:
        return joblib.load(file_path)
    except Exception:
        logger.debug("joblib.load failed for %s, falling back to pickle", file_path)
        with open(file_path, "rb") as fh:
            return pickle.load(fh)  # noqa: S301 — trusted artifact from our training pipeline


def load_artifacts() -> Tuple[Any, Any]:
    """Load model artifact with thread-safe caching.

    The full Pipeline (best_model.pkl) contains preprocessing internally,
    so preprocessor.pkl is not loaded separately.

    Returns:
        Tuple of (model, None) — second element kept for backwards compatibility.

    Raises:
        FileNotFoundError: If the model path does not exist.
        Exception: On deserialization failure.
    """
    global _model, _loaded

    if _loaded:
        return _model, None

    with _load_lock:
        if _loaded:
            return _model, None

        _ensure_pipeline_shim()

        logger.info(
            "Loading fraud detection model from %s", fraud_config.model_path
        )
        _model = _load_pickle(fraud_config.model_path)
        logger.info(
            "Model loaded: type=%s", type(_model).__name__
        )

        _loaded = True
        return _model, None


def get_model() -> Any:
    """Return the loaded model (loads on first call)."""
    model, _ = load_artifacts()
    return model


def get_preprocessing() -> None:
    """No longer loads preprocessor.pkl — the full Pipeline in best_model.pkl
    contains preprocessing internally."""
    return None


def is_loaded() -> bool:
    """Check if artifacts have been loaded without triggering a load."""
    return _loaded


def reset() -> None:
    """Reset the cache — primarily used in tests.

    After calling this, the next access to get_model() / get_preprocessing()
    will reload from disk.
    """
    global _model, _loaded
    with _load_lock:
        _model = None
        _loaded = False
        logger.info("Model loader cache reset")
