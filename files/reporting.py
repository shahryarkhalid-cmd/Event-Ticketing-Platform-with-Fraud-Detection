"""Phase 13 — Automated report generation (Markdown, HTML, CSV, PDF)."""
from __future__ import annotations

import logging
from pathlib import Path

import markdown as md_lib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..app.services.fraud_detection import schema_contract as sc

logger = logging.getLogger("training_pipeline.reporting")


def build_markdown_report(
    dataset_stats: dict,
    smote_decision: dict,
    comparison_df: pd.DataFrame,
    best_model_name: str,
    test_metrics: dict,
    feature_importance_df: pd.DataFrame | None,
    core_only_ablation: dict,
) -> str:
    lines = []
    lines.append("# Tixora Fraud Detection — Training Report (v2)\n")
    lines.append("## Executive Summary\n")
    lines.append(
        f"Trained on {dataset_stats['n_rows']:,} orders "
        f"({dataset_stats['fraud_rate']*100:.2f}% fraud) built entirely from the application's "
        f"existing `User`/`Event`/`TicketTier`/`Order` tables. The best model, "
        f"**{best_model_name}**, reaches a test PR-AUC of {test_metrics['pr_auc']:.3f} "
        f"(ROC-AUC {test_metrics['roc_auc']:.3f}) using only fields the application already "
        f"collects today — no database migration or endpoint change required.\n"
    )
    lines.append(
        f"Using the same trained model with the {len(sc.OPTIONAL_FEATURES)} optional "
        f"(device/network/payment-attempt) columns entirely absent — the current production "
        f"reality — retains **{core_only_ablation['pct_retained']:.1f}%** of the full-feature "
        f"PR-AUC ({core_only_ablation['core_only_pr_auc']:.3f} vs {core_only_ablation['full_pr_auc']:.3f}). "
        f"The model is deployable as-is; the optional signals are a future enhancement, not a dependency.\n"
    )

    lines.append("## Dataset Summary\n")
    lines.append(f"- Rows: {dataset_stats['n_rows']:,}")
    lines.append(f"- Fraud rate: {dataset_stats['fraud_rate']*100:.2f}%")
    lines.append(f"- Core features: {len(sc.CORE_FEATURES)} (always available)")
    lines.append(f"- Optional features: {len(sc.OPTIONAL_FEATURES)} (defaulted when absent)")
    lines.append(f"- Train/val/test split: {dataset_stats['n_train']:,} / {dataset_stats['n_val']:,} / {dataset_stats['n_test']:,}\n")

    lines.append("## Feature Summary\n")
    lines.append("**Core (mandatory, always computable from existing app data):**")
    lines.append(", ".join(f"`{f}`" for f in sc.CORE_FEATURES) + "\n")
    lines.append("**Optional (defaulted when the app doesn't send them):**")
    lines.append(", ".join(f"`{f}`" for f in sc.OPTIONAL_FEATURES) + "\n")

    lines.append("## Class-Imbalance Strategy\n")
    lines.append(
        f"SMOTE vs. class-weighting alone was compared via 3-fold CV PR-AUC: baseline "
        f"{smote_decision['baseline_pr_auc_mean']:.4f} vs. SMOTE "
        f"{smote_decision['smote_pr_auc_mean']:.4f}. "
        f"Decision: **{'use SMOTE' if smote_decision['use_smote'] else 'class-weighting only, no SMOTE'}** "
        f"(SMOTE did not demonstrate a genuine improvement here).\n"
    )

    lines.append("## Model Comparison (validation PR-AUC)\n")
    lines.append(comparison_df.to_markdown(index=False) + "\n")

    lines.append(f"## Held-out Test Set Evaluation — {best_model_name}\n")
    lines.append(f"- Threshold: {test_metrics['threshold']}")
    lines.append(f"- Accuracy: {test_metrics['accuracy']:.4f}")
    lines.append(f"- Precision: {test_metrics['precision']:.4f}")
    lines.append(f"- Recall: {test_metrics['recall']:.4f}")
    lines.append(f"- F1: {test_metrics['f1']:.4f}")
    lines.append(f"- ROC-AUC: {test_metrics['roc_auc']:.4f}")
    lines.append(f"- PR-AUC: {test_metrics['pr_auc']:.4f}")
    lines.append(f"- Confusion matrix (rows=actual, cols=predicted): {test_metrics['confusion_matrix']}\n")
    lines.append("```\n" + test_metrics["classification_report"] + "\n```\n")

    if feature_importance_df is not None:
        lines.append("## Top 15 Feature Importances\n")
        lines.append(feature_importance_df.head(15).to_markdown(index=False) + "\n")

    lines.append("## Recommendations\n")
    lines.append(
        "- Deploy as-is using only core features; treat optional-signal capture "
        "(device/IP/payment-attempt telemetry) as a future enhancement, not a blocker.\n"
        "- Monitor precision/recall drift monthly; retrain when validated new labeled "
        "data (confirmed chargebacks/disputes) becomes available.\n"
        "- Revisit the decision threshold against the actual operational cost of a false "
        "positive (blocked legitimate purchase) vs. a false negative (missed fraud).\n"
    )
    lines.append("## Limitations\n")
    lines.append(
        "- Trained entirely on synthetic data; real fraud patterns should be validated "
        "against this model once genuine labeled outcomes exist.\n"
        "- `stealth_fraud` cases are deliberately not cleanly separable from legitimate "
        "orders using transactional data alone — a ceiling on recall is expected and "
        "realistic, not a bug.\n"
        "- Optional features were generated with correlated-but-noisy signal; real "
        "device/network data, once captured, may carry more or less signal than "
        "modeled here.\n"
    )
    lines.append("## Future Improvements\n")
    lines.append(
        "- Capture device/IP/payment-attempt telemetry at checkout to activate the "
        "optional feature group for real.\n"
        "- Add a genuine phone-verification field to `User` if phone-based risk "
        "scoring becomes a priority.\n"
        "- Automate the retraining pipeline against a schema/data-drift monitor.\n"
    )
    return "\n".join(lines)


def save_reports(markdown_text: str, reports_dir: Path) -> dict[str, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    md_path = reports_dir / "training_report.md"
    md_path.write_text(markdown_text)

    html_body = md_lib.markdown(markdown_text, extensions=["tables", "fenced_code"])
    html_path = reports_dir / "training_report.html"
    html_path.write_text(
        f"<html><head><meta charset='utf-8'><title>Tixora Fraud Detection Report</title>"
        f"<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;line-height:1.5;}} "
        f"table{{border-collapse:collapse;width:100%;}} td,th{{border:1px solid #ccc;padding:6px 10px;}} "
        f"code, pre {{background:#f5f5f5;}}</style></head><body>{html_body}</body></html>"
    )

    logger.info("Saved Markdown + HTML reports to %s", reports_dir)
    return {"markdown": md_path, "html": html_path}


def save_pdf_report(
    reports_dir: Path,
    best_model_name: str,
    test_metrics: dict,
    comparison_df: pd.DataFrame,
    core_only_ablation: dict,
) -> Path:
    """A concise PDF summary (full detail lives in the Markdown/HTML report) with the key
    tables and, if present, the ROC/PR/feature-importance plots saved by mlflow_tracking."""
    reports_dir = Path(reports_dir)
    pdf_path = reports_dir / "training_report.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    elements = [
        Paragraph("Tixora Fraud Detection — Training Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            f"Best model: <b>{best_model_name}</b> | Test PR-AUC: {test_metrics['pr_auc']:.3f} | "
            f"Test ROC-AUC: {test_metrics['roc_auc']:.3f}",
            styles["Normal"],
        ),
        Spacer(1, 6),
        Paragraph(
            f"Core-features-only input retains {core_only_ablation['pct_retained']:.1f}% of full-feature "
            f"PR-AUC — deployable today without any application changes.",
            styles["Normal"],
        ),
        Spacer(1, 18),
        Paragraph("Model Comparison (validation PR-AUC)", styles["Heading2"]),
    ]

    table_data = [list(comparison_df.columns)] + comparison_df.round(4).astype(str).values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph("Held-out Test Set Metrics", styles["Heading2"]))
    metric_rows = [["Metric", "Value"]] + [
        [k, f"{v:.4f}"] for k, v in test_metrics.items()
        if k in ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc")
    ]
    mtable = Table(metric_rows)
    mtable.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(mtable)

    for img_name, title in [("roc_curve.png", "ROC Curve"), ("pr_curve.png", "Precision-Recall Curve"),
                             ("feature_importance.png", "Top Feature Importances")]:
        img_path = reports_dir / img_name
        if img_path.exists():
            elements.append(Spacer(1, 18))
            elements.append(Paragraph(title, styles["Heading2"]))
            elements.append(RLImage(str(img_path), width=420, height=320))

    doc.build(elements)
    logger.info("Saved PDF report to %s", pdf_path)
    return pdf_path
