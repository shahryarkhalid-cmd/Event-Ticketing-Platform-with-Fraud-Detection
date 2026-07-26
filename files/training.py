"""
Phase 6 — Stratified train/validation/test split.
Phase 8 — Multi-model training with class-imbalance handling.
Phase 9 — Hyperparameter optimization of the strongest candidates only.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from .preprocessing import build_preprocessing_pipeline

logger = logging.getLogger("training_pipeline.training")

RANDOM_STATE = 42


@dataclass
class DataSplits:
    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series


def split_data(X: pd.DataFrame, y: pd.Series) -> DataSplits:
    """70/15/15 stratified split. Test set is held out untouched until final evaluation."""
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE
    )
    logger.info(
        "Split sizes — train: %s (%.2f%% fraud), val: %s (%.2f%% fraud), test: %s (%.2f%% fraud)",
        len(X_train), 100 * y_train.mean(), len(X_val), 100 * y_val.mean(), len(X_test), 100 * y_test.mean(),
    )
    return DataSplits(X_train, X_val, X_test, y_train, y_val, y_test)


def model_registry(scale_pos_weight: float) -> dict:
    """Every model uses class-imbalance handling native to its own API (no SMOTE baked in here)."""
    return {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, class_weight="balanced", n_jobs=-1, random_state=RANDOM_STATE
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=300, class_weight="balanced", n_jobs=-1, random_state=RANDOM_STATE
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            class_weight="balanced", random_state=RANDOM_STATE
        ),
        "xgboost": XGBClassifier(
            n_estimators=300, scale_pos_weight=scale_pos_weight, eval_metric="logloss",
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=300, class_weight="balanced", random_state=RANDOM_STATE, verbosity=-1, n_jobs=-1
        ),
        "catboost": CatBoostClassifier(
            iterations=300, auto_class_weights="Balanced", random_state=RANDOM_STATE, verbose=False
        ),
    }


def evaluate_smote_benefit(X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """
    Phase 8 instruction: only use SMOTE if it demonstrably helps. Uses a
    single representative model (logistic regression, most sensitive to
    class balance of the candidates) under 3-fold CV, comparing
    class-weighting alone vs. SMOTE + class-weighting, on PR-AUC (the right
    metric for a ~4% positive rate).
    """
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)

    baseline_pipe = Pipeline([
        ("preprocess", build_preprocessing_pipeline()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE)),
    ])
    smote_pipe = ImbPipeline(
        list(build_preprocessing_pipeline().steps)
        + [("smote", SMOTE(random_state=RANDOM_STATE)),
           ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE))]
    )

    baseline_scores = cross_val_score(baseline_pipe, X_train, y_train, cv=cv, scoring="average_precision")
    smote_scores = cross_val_score(smote_pipe, X_train, y_train, cv=cv, scoring="average_precision")

    result = {
        "baseline_pr_auc_mean": float(baseline_scores.mean()),
        "baseline_pr_auc_std": float(baseline_scores.std()),
        "smote_pr_auc_mean": float(smote_scores.mean()),
        "smote_pr_auc_std": float(smote_scores.std()),
        "use_smote": bool(smote_scores.mean() > baseline_scores.mean() + 0.005),  # require a real margin
    }
    logger.info(
        "SMOTE evaluation — baseline PR-AUC: %.4f +/- %.4f | SMOTE PR-AUC: %.4f +/- %.4f | decision: use_smote=%s",
        result["baseline_pr_auc_mean"], result["baseline_pr_auc_std"],
        result["smote_pr_auc_mean"], result["smote_pr_auc_std"], result["use_smote"],
    )
    return result


def build_full_pipeline(classifier, use_smote: bool) -> Pipeline:
    """Wrap a classifier with the shared preprocessing (+ optional SMOTE) into one fittable pipeline."""
    if use_smote:
        return ImbPipeline(
            list(build_preprocessing_pipeline().steps)
            + [("smote", SMOTE(random_state=RANDOM_STATE)), ("classifier", classifier)]
        )
    return Pipeline([
        ("preprocess", build_preprocessing_pipeline()),
        ("classifier", classifier),
    ])


def train_all_models(splits: DataSplits, use_smote: bool) -> dict:
    """Fit every model in the registry, score on validation set, return fitted pipelines + metrics."""
    scale_pos_weight = (splits.y_train == 0).sum() / max((splits.y_train == 1).sum(), 1)
    registry = model_registry(scale_pos_weight)

    results = {}
    for name, clf in registry.items():
        t0 = time.time()
        pipe = build_full_pipeline(clf, use_smote=use_smote)
        pipe.fit(splits.X_train, splits.y_train)
        val_proba = pipe.predict_proba(splits.X_val)[:, 1]
        pr_auc = average_precision_score(splits.y_val, val_proba)
        elapsed = time.time() - t0
        results[name] = {"pipeline": pipe, "val_pr_auc": pr_auc, "train_seconds": elapsed}
        logger.info("Trained %-24s val PR-AUC=%.4f (%.1fs)", name, pr_auc, elapsed)

    return results


PARAM_DISTRIBUTIONS = {
    "random_forest": {
        "classifier__n_estimators": [200, 300, 400, 600],
        "classifier__max_depth": [None, 8, 12, 20],
        "classifier__min_samples_leaf": [1, 2, 4, 8],
        "classifier__max_features": ["sqrt", "log2", None],
    },
    "extra_trees": {
        "classifier__n_estimators": [200, 300, 400, 600],
        "classifier__max_depth": [None, 8, 12, 20],
        "classifier__min_samples_leaf": [1, 2, 4, 8],
    },
    "hist_gradient_boosting": {
        "classifier__max_iter": [150, 250, 400],
        "classifier__max_depth": [None, 6, 10, 16],
        "classifier__learning_rate": [0.02, 0.05, 0.1, 0.2],
        "classifier__l2_regularization": [0.0, 0.1, 1.0],
    },
    "xgboost": {
        "classifier__n_estimators": [200, 300, 500],
        "classifier__max_depth": [3, 5, 7, 9],
        "classifier__learning_rate": [0.02, 0.05, 0.1, 0.2],
        "classifier__subsample": [0.7, 0.85, 1.0],
        "classifier__colsample_bytree": [0.7, 0.85, 1.0],
    },
    "lightgbm": {
        "classifier__n_estimators": [200, 300, 500],
        "classifier__num_leaves": [15, 31, 63, 127],
        "classifier__learning_rate": [0.02, 0.05, 0.1, 0.2],
        "classifier__subsample": [0.7, 0.85, 1.0],
    },
    "catboost": {
        "classifier__depth": [4, 6, 8, 10],
        "classifier__learning_rate": [0.02, 0.05, 0.1],
        "classifier__l2_leaf_reg": [1, 3, 5, 9],
    },
    "logistic_regression": {
        "classifier__C": [0.01, 0.1, 1.0, 10.0],
        "classifier__penalty": ["l2"],
    },
}


def tune_top_models(
    splits: DataSplits, trained_results: dict, use_smote: bool, top_k: int = 2, n_iter: int = 15
) -> dict:
    """Phase 9: RandomizedSearchCV on only the top_k models by validation PR-AUC."""
    ranked = sorted(trained_results.items(), key=lambda kv: kv[1]["val_pr_auc"], reverse=True)
    top_names = [name for name, _ in ranked[:top_k]]
    logger.info("Tuning top %s model(s) by validation PR-AUC: %s", top_k, top_names)

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    tuned = {}
    scale_pos_weight = (splits.y_train == 0).sum() / max((splits.y_train == 1).sum(), 1)

    for name in top_names:
        base_clf = model_registry(scale_pos_weight)[name]
        pipe = build_full_pipeline(base_clf, use_smote=use_smote)
        param_dist = PARAM_DISTRIBUTIONS.get(name, {})
        if not param_dist:
            tuned[name] = trained_results[name]
            continue

        t0 = time.time()
        search = RandomizedSearchCV(
            pipe, param_distributions=param_dist, n_iter=n_iter, cv=cv,
            scoring="average_precision", random_state=RANDOM_STATE, n_jobs=-1, refit=True,
        )
        search.fit(splits.X_train, splits.y_train)
        val_proba = search.best_estimator_.predict_proba(splits.X_val)[:, 1]
        pr_auc = average_precision_score(splits.y_val, val_proba)
        elapsed = time.time() - t0

        tuned[name] = {
            "pipeline": search.best_estimator_,
            "val_pr_auc": pr_auc,
            "best_params": search.best_params_,
            "train_seconds": elapsed,
        }
        logger.info(
            "Tuned %-24s val PR-AUC=%.4f (was %.4f) best_params=%s (%.1fs)",
            name, pr_auc, trained_results[name]["val_pr_auc"], search.best_params_, elapsed,
        )

    for name, res in trained_results.items():
        if name not in tuned:
            tuned[name] = res
    return tuned
