"""Phase 11 — MLflow experiment tracking."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import matplotlib.pyplot as plt
import mlflow
import pandas as pd

logger = logging.getLogger("training_pipeline.mlflow_tracking")


def init_mlflow(tracking_dir: Path, experiment_name: str = "tixora_fraud_detection_v2") -> None:
    tracking_dir.mkdir(parents=True, exist_ok=True)
    db_path = tracking_dir / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{db_path.resolve()}")
    mlflow.set_experiment(experiment_name)


def log_model_run(name: str, result: dict, splits, smote_used: bool, git_commit: str | None) -> str:
    """Log one trained candidate's params/metrics/artifacts as an MLflow run. Returns the run_id."""
    with mlflow.start_run(run_name=name) as run:
        clf = result["pipeline"].named_steps["classifier"]
        params = {k: v for k, v in clf.get_params().items() if isinstance(v, (int, float, str, bool)) or v is None}
        mlflow.log_params(params)
        mlflow.log_param("smote_used", smote_used)
        if git_commit:
            mlflow.log_param("git_commit", git_commit)
        if "best_params" in result:
            mlflow.log_params({f"tuned__{k}": v for k, v in result["best_params"].items()})

        mlflow.log_metric("val_pr_auc", result["val_pr_auc"])
        mlflow.log_metric("train_seconds", result["train_seconds"])
        mlflow.log_metric("train_rows", len(splits.X_train))
        mlflow.log_metric("val_rows", len(splits.X_val))

        return run.info.run_id


def log_final_model(
    fraud_pipeline, test_metrics: dict, comparison_df: pd.DataFrame,
    curves: dict, feature_importance_df: pd.DataFrame | None, reports_dir: Path,
) -> str:
    """Log the selected best model with full test-set evaluation artifacts, and register it."""
    with mlflow.start_run(run_name=f"BEST_{fraud_pipeline.model_name}") as run:
        mlflow.log_param("model_name", fraud_pipeline.model_name)
        mlflow.log_param("decision_threshold", fraud_pipeline.decision_threshold)

        for k, v in test_metrics.items():
            if isinstance(v, (int, float)):
                mlflow.log_metric(f"test_{k}", v)

        comparison_path = reports_dir / "model_comparison.csv"
        comparison_df.to_csv(comparison_path, index=False)
        mlflow.log_artifact(str(comparison_path))

        if feature_importance_df is not None:
            fi_path = reports_dir / "feature_importance.csv"
            feature_importance_df.to_csv(fi_path, index=False)
            mlflow.log_artifact(str(fi_path))

            fig, ax = plt.subplots(figsize=(8, 6))
            top = feature_importance_df.head(20).iloc[::-1]
            ax.barh(top["feature"], top["importance"])
            ax.set_title("Top 20 feature importances")
            fig.tight_layout()
            fig_path = reports_dir / "feature_importance.png"
            fig.savefig(fig_path, dpi=120)
            plt.close(fig)
            mlflow.log_artifact(str(fig_path))

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(curves["roc"]["fpr"], curves["roc"]["tpr"], label=f"ROC (AUC={test_metrics['roc_auc']:.3f})")
        ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
        ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate"); ax.legend()
        ax.set_title("ROC Curve — held-out test set")
        fig.tight_layout()
        roc_path = reports_dir / "roc_curve.png"
        fig.savefig(roc_path, dpi=120)
        plt.close(fig)
        mlflow.log_artifact(str(roc_path))

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(curves["pr"]["recall"], curves["pr"]["precision"], label=f"PR (AUC={test_metrics['pr_auc']:.3f})")
        ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.legend()
        ax.set_title("Precision-Recall Curve — held-out test set")
        fig.tight_layout()
        pr_path = reports_dir / "pr_curve.png"
        fig.savefig(pr_path, dpi=120)
        plt.close(fig)
        mlflow.log_artifact(str(pr_path))

        mlflow.sklearn.log_model(
            fraud_pipeline.fitted_pipeline, name="model", registered_model_name="tixora_fraud_detector",
            serialization_format="cloudpickle",
        )
        logger.info("Logged and registered final model under MLflow run %s", run.info.run_id)
        return run.info.run_id
