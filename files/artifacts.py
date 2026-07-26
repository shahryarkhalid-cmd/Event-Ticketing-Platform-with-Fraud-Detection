"""Phase 15 — Save every production artifact."""
from __future__ import annotations

import json
import logging
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from ..app.services.fraud_detection import schema_contract as sc

logger = logging.getLogger("training_pipeline.artifacts")


def _git_commit_hash() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, cwd=Path(__file__).parent
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def save_all_artifacts(
    artifacts_dir: Path,
    fraud_pipeline,
    best_model_name: str,
    tuned_results: dict,
    test_metrics: dict,
    smote_decision: dict,
    training_seconds: float,
) -> None:
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # trained_pipeline.pkl / best_model.pkl — the full, ready-to-serve wrapper
    fraud_pipeline.save(artifacts_dir / "trained_pipeline.pkl")
    joblib.dump(fraud_pipeline.fitted_pipeline, artifacts_dir / "best_model.pkl")

    # preprocessor.pkl — the preprocessing half alone, for reuse/inspection
    joblib.dump(fraud_pipeline.fitted_pipeline.named_steps["preprocess"], artifacts_dir / "preprocessor.pkl")

    # feature_names.pkl / feature_list.json
    from .evaluation import get_feature_names
    feature_names = get_feature_names(fraud_pipeline.fitted_pipeline)
    joblib.dump(feature_names, artifacts_dir / "feature_names.pkl")

    manifest = sc.SchemaManifest()
    with open(artifacts_dir / "feature_list.json", "w") as f:
        json.dump({"post_encoding_feature_names": feature_names, **manifest.to_dict()}, f, indent=2)

    # model_metadata.json
    metadata = {
        "model_name": best_model_name,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_commit": _git_commit_hash(),
        "training_seconds_total": training_seconds,
        "smote_decision": smote_decision,
        "test_metrics": {k: v for k, v in test_metrics.items() if k != "classification_report"},
        "decision_threshold": fraud_pipeline.decision_threshold,
    }
    with open(artifacts_dir / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    # training_config.json
    config = {
        "random_state": 42,
        "split": {"train": 0.70, "val": 0.15, "test": 0.15},
        "model_candidates": list(tuned_results.keys()),
        "selection_criterion": "highest validation PR-AUC (average precision)",
        "core_features": sc.CORE_FEATURES,
        "optional_features": sc.OPTIONAL_FEATURES,
    }
    with open(artifacts_dir / "training_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # requirements.txt for this ml_v2 environment
    import xgboost, lightgbm, catboost, sklearn, imblearn, shap, mlflow
    pins = {
        "pandas": pd.__version__, "numpy": __import__("numpy").__version__,
        "scikit-learn": sklearn.__version__, "xgboost": xgboost.__version__,
        "lightgbm": lightgbm.__version__, "catboost": catboost.__version__,
        "imbalanced-learn": imblearn.__version__, "shap": shap.__version__,
        "mlflow": mlflow.__version__, "joblib": joblib.__version__,
    }
    with open(artifacts_dir / "requirements.txt", "w") as f:
        f.write("\n".join(f"{k}=={v}" for k, v in pins.items()) + "\n")

    logger.info("Saved all Phase-15 artifacts to %s", artifacts_dir)
    logger.info("Artifact files: %s", sorted(p.name for p in artifacts_dir.glob("*")))
