# Tixora Fraud Detection — Production Pipeline (v2)

Upgrades the Stage-1 schema + synthetic dataset into a full production
training pipeline, per the "Production Fraud Detection Pipeline Upgrade" spec.

## The central design decision

**The application's DB, API, and frontend are never modified.** Every
feature the model requires at inference time (`CORE_FEATURES`, see
`pipeline/schema_contract.py`) is already computable from the existing
`User` / `Event` / `TicketTier` / `Order` tables. A second set of
`OPTIONAL_FEATURES` (device, network, payment-attempt, phone-verification
signals) is engineered from a synthetic enrichment table for training
richness, but is **never required** — the pipeline substitutes a documented
safe default (0 / "Unknown" / False) for any optional column that's missing,
identically at training time and inference time.

**Result, measured on the held-out test set:** the deployed model, using
*only* the fields the app already sends, retains **99.1%** of its full
PR-AUC (0.818 vs 0.825). The optional signals are a genuine but small
enhancement, not a dependency — you can deploy this today.

## What's in this package

```
SCHEMA.md                       Stage-1 schema write-up (still accurate for CORE features)
Tixora_train_v2.ipynb           The full production notebook — runs top to bottom, no manual edits
data_generation/                Synthetic data generators (Stage 1 + new enrichment.py)
data/                           users/events/ticket_tiers/orders/order_enrichment CSVs + merged master_dataset.parquet
pipeline/                       Reusable production modules (see below)
artifacts/                      Trained model + preprocessing pipeline + metadata, ready to load in the app
reports/                        training_report.{md,html,pdf}, model_comparison.csv, feature_importance.csv, plots
logs/training.log               Full run log — every stage, timing, memory, warnings
```

### `pipeline/` modules (each independently reusable, not just notebook glue)

| Module | Phase(s) | Purpose |
|---|---|---|
| `schema_contract.py` | 2, 7 | The core/optional feature contract + `align_to_schema()` — the graceful-degradation mechanism |
| `merge.py` | 2 | Joins the 5 CSVs into one master dataset, dtype-optimized, deduplicated |
| `feature_engineering.py` | 3, 4 | All engineered features, leakage-safe (time-respecting velocity, no current-order-outcome fields) |
| `preprocessing.py` | 5, 7 | Cleaning + `SchemaAlignerTransformer` + ColumnTransformer (impute/encode/scale) |
| `training.py` | 6, 8, 9 | Stratified split, 7-model zoo, SMOTE-vs-class-weight evaluation, RandomizedSearchCV tuning |
| `evaluation.py` | 10 | Every requested metric/curve, SHAP, threshold analysis, FP/FN analysis, model selection |
| `mlflow_tracking.py` | 11 | Per-model MLflow runs + final model registration |
| `logging_utils.py` | 12 | Centralized logging with per-stage timing/memory |
| `reporting.py` | 13 | Markdown / HTML / PDF report generation |
| `inference.py` | 14 | `FraudDetectionPipeline` — the one class the FastAPI app imports |
| `artifacts.py` | 15 | Saves every artifact the spec asked for |

## Using the trained model in the FastAPI app

```python
from pipeline.inference import FraudDetectionPipeline

fraud_pipeline = FraudDetectionPipeline.load("artifacts/trained_pipeline.pkl")

# In app/services/Order_services.py, inside book_ticket(), with whatever
# User/Event/TicketTier context is already in scope:
order_context = {
    "quantity": order_data.quantity,
    "total_price": total_price,
    "account_age_days": (now - user.created_at).total_seconds() / 86400,
    "is_verified": user.is_verified,
    # ... the remaining CORE_FEATURES — see pipeline/schema_contract.py
}
fraud_score = fraud_pipeline.predict_proba(order_context)[0]
```

No new columns, no new endpoints, no frontend change required to start
scoring orders today.

## Key decisions made along the way (documented, not hidden)

- **SMOTE was evaluated and rejected**: 3-fold CV PR-AUC was *worse* with
  SMOTE (0.569) than with class-weighting alone (0.585) on this data —
  see `reports/training_report.md` for the numbers.
- **`status` and `has_qr_code` are excluded from the model entirely.**
  Both are only known *after* the fraud decision would actually be made in
  production (payment settlement, QR generation) — leaving them in would
  have been leakage, since several fraud archetypes are partly defined by
  their eventual status.
- **Best model: XGBoost** (tuned), selected by validation PR-AUC — the
  right metric here since fraud is ~4% of orders (accuracy and even
  ROC-AUC are easy to misread under that imbalance).
- **`email_domain_risk` / `disposable_email`**, though technically
  derivable from the app's existing `User.email` field, were **not**
  generated in the Stage-1 synthetic dataset (email was excluded there as
  direct PII). They're absent from `CORE_FEATURES` here for that reason —
  flagging this explicitly rather than silently treating them as optional.
