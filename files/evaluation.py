"""
Phase 10 — Comprehensive evaluation.

Everything here operates on a fitted full pipeline (preprocessing + model)
and the held-out TEST set, which is touched only once model selection has
already happened on the validation set (see training.py / the notebook).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, classification_report,
    f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score, roc_curve,
)

logger = logging.getLogger("training_pipeline.evaluation")


def select_best_model(results: dict) -> str:
    """
    Selection criterion: highest validation PR-AUC (average precision).
    PR-AUC rather than ROC-AUC or accuracy because the positive class is
    ~4% of the data — ROC-AUC is easy to inflate under heavy imbalance,
    and accuracy is close to meaningless (predicting "not fraud" always
    scores ~96%).
    """
    best_name = max(results, key=lambda k: results[k]["val_pr_auc"])
    logger.info("Best model selected by validation PR-AUC: %s (%.4f)", best_name, results[best_name]["val_pr_auc"])
    return best_name


def evaluate_on_test(pipeline, X_test: pd.DataFrame, y_test: pd.Series, threshold: float = 0.5) -> dict:
    proba = pipeline.predict_proba(X_test)[:, 1]
    preds = (proba >= threshold).astype(int)

    metrics = {
        "threshold": threshold,
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "recall": recall_score(y_test, preds, zero_division=0),
        "f1": f1_score(y_test, preds, zero_division=0),
        "roc_auc": roc_auc_score(y_test, proba),
        "pr_auc": average_precision_score(y_test, proba),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
        "classification_report": classification_report(y_test, preds, zero_division=0, digits=3),
    }
    logger.info(
        "Test set @ threshold=%.2f — accuracy=%.4f precision=%.4f recall=%.4f f1=%.4f roc_auc=%.4f pr_auc=%.4f",
        threshold, metrics["accuracy"], metrics["precision"], metrics["recall"],
        metrics["f1"], metrics["roc_auc"], metrics["pr_auc"],
    )
    return metrics


def curve_data(pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    proba = pipeline.predict_proba(X_test)[:, 1]
    fpr, tpr, roc_thresholds = roc_curve(y_test, proba)
    precision, recall, pr_thresholds = precision_recall_curve(y_test, proba)
    frac_pos, mean_pred = calibration_curve(y_test, proba, n_bins=10, strategy="quantile")
    return {
        "roc": {"fpr": fpr, "tpr": tpr, "thresholds": roc_thresholds},
        "pr": {"precision": precision, "recall": recall, "thresholds": pr_thresholds},
        "calibration": {"fraction_of_positives": frac_pos, "mean_predicted": mean_pred},
        "proba": proba,
    }


def threshold_analysis(y_test: pd.Series, proba: np.ndarray, thresholds=None) -> pd.DataFrame:
    """Precision/recall/F1/flagged-volume at a range of decision thresholds."""
    if thresholds is None:
        thresholds = np.arange(0.05, 0.95, 0.05)
    rows = []
    for t in thresholds:
        preds = (proba >= t).astype(int)
        rows.append({
            "threshold": round(float(t), 2),
            "precision": precision_score(y_test, preds, zero_division=0),
            "recall": recall_score(y_test, preds, zero_division=0),
            "f1": f1_score(y_test, preds, zero_division=0),
            "flagged_rate": preds.mean(),
        })
    return pd.DataFrame(rows)


def get_feature_names(fitted_pipeline) -> list[str]:
    """Recover human-readable feature names after schema alignment + one-hot encoding."""
    preprocess = fitted_pipeline.named_steps.get("preprocess")
    ct = preprocess.named_steps["preprocess"]
    return list(ct.get_feature_names_out())


def feature_importance(fitted_pipeline) -> pd.DataFrame | None:
    """Native feature importance for tree-based models; None for models without one (e.g. logistic uses coef_)."""
    clf = fitted_pipeline.named_steps["classifier"]
    names = get_feature_names(fitted_pipeline)

    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        importances = np.abs(clf.coef_).ravel()
    else:
        return None

    return (
        pd.DataFrame({"feature": names, "importance": importances})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def false_positive_negative_analysis(
    X_test: pd.DataFrame, y_test: pd.Series, proba: np.ndarray, threshold: float = 0.5, top_n: int = 15
) -> dict:
    preds = (proba >= threshold).astype(int)
    y_arr = y_test.to_numpy()

    fp_mask = (preds == 1) & (y_arr == 0)
    fn_mask = (preds == 0) & (y_arr == 1)

    fp_rows = X_test.loc[fp_mask].assign(predicted_proba=proba[fp_mask]).sort_values(
        "predicted_proba", ascending=False
    ).head(top_n)
    fn_rows = X_test.loc[fn_mask].assign(predicted_proba=proba[fn_mask]).sort_values(
        "predicted_proba", ascending=True
    ).head(top_n)

    return {
        "n_false_positives": int(fp_mask.sum()),
        "n_false_negatives": int(fn_mask.sum()),
        "false_positive_rate": float(fp_mask.sum() / max((y_arr == 0).sum(), 1)),
        "false_negative_rate": float(fn_mask.sum() / max((y_arr == 1).sum(), 1)),
        "top_false_positives": fp_rows,
        "top_false_negatives": fn_rows,
    }


def compute_shap_values(fitted_pipeline, X_sample: pd.DataFrame, max_rows: int = 500):
    """
    SHAP explanation for the (necessarily tree-based, for TreeExplainer
    speed) best model, on a bounded sample for runtime. Returns None
    gracefully for model types SHAP's TreeExplainer doesn't support here.
    """
    import shap

    clf = fitted_pipeline.named_steps["classifier"]
    if not hasattr(clf, "feature_importances_"):
        logger.info("SHAP skipped: %s is not a tree-based model with native TreeExplainer support", type(clf).__name__)
        return None, None

    preprocess = fitted_pipeline.named_steps["preprocess"]
    sample = X_sample.sample(n=min(max_rows, len(X_sample)), random_state=42)
    X_transformed = preprocess.transform(sample)
    names = get_feature_names(fitted_pipeline)

    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X_transformed)
    if isinstance(shap_values, list):  # some tree explainers return per-class list
        shap_values = shap_values[1]
    return shap_values, pd.DataFrame(
        X_transformed if not hasattr(X_transformed, "toarray") else X_transformed.toarray(), columns=names
    )


def build_comparison_table(results: dict) -> pd.DataFrame:
    rows = [
        {
            "model": name,
            "val_pr_auc": r["val_pr_auc"],
            "train_seconds": r["train_seconds"],
            "tuned": "best_params" in r,
        }
        for name, r in results.items()
    ]
    return pd.DataFrame(rows).sort_values("val_pr_auc", ascending=False).reset_index(drop=True)
