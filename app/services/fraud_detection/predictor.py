"""Fraud prediction orchestrator.

Ties together model loading, feature engineering, and inference
into a single ``predict()`` call.  Handles all error cases with
configurable fail-open behaviour so that a broken model never blocks
legitimate orders.
"""

from __future__ import annotations

import logging

import numpy as np

from .config import fraud_config
from .feature_builder import build_features
from .model_loader import get_model, is_loaded
from .schemas import FraudPrediction, OrderContext

logger = logging.getLogger(__name__)


def predict(ctx: OrderContext) -> FraudPrediction:
    """Run fraud prediction on an order context.

    This is the main entry point for the prediction pipeline.

    Args:
        ctx: The order context to evaluate.

    Returns:
        A ``FraudPrediction`` with the result.  If the service is
        disabled, the model cannot be loaded, or any error occurs,
        a clean (non-fraud) prediction is returned (fail-open).
    """
    # Fast exit if disabled
    if not fraud_config.enabled:
        logger.debug("Fraud detection disabled — returning clean prediction")
        return FraudPrediction(
            is_fraud=False,
            fraud_probability=0.0,
            model_name="disabled",
            reason="Fraud detection service is disabled",
        )

    try:
        return _run_prediction(ctx)
    except Exception:
        logger.exception("Fraud prediction failed unexpectedly")
        if fraud_config.fallback_on_error:
            return FraudPrediction(
                is_fraud=False,
                fraud_probability=0.0,
                model_name=fraud_config.model_name,
                reason="Prediction failed — fail-open",
            )
        raise


def _run_prediction(ctx: OrderContext) -> FraudPrediction:
    """Internal prediction logic (may raise)."""
    logger.info(
        "Starting fraud prediction for user=%s event=%s quantity=%d total=%.2f",
        ctx.user_id,
        ctx.event_id,
        ctx.quantity,
        ctx.total_price,
    )
    # Load model (cached after first call)
    try:
        model = get_model()
        logger.info(
        "Fraud model loaded successfully: %s",
        fraud_config.model_name,
        )
    except FileNotFoundError as exc:
        logger.warning(
            "Model artifacts not found: %s — returning clean prediction",
            exc,
        )
        return FraudPrediction(
            is_fraud=False,
            fraud_probability=0.0,
            model_name="none",
            reason=f"Model artifacts not found: {exc}",
        )

    # Build features (the full Pipeline in best_model.pkl handles schema
    # alignment, cleaning, encoding, and scaling internally)
    features_df = build_features(ctx)
    logger.debug(
        "Features built for user=%s event=%s: shape=%s",
        ctx.user_id,
        ctx.event_id,
        features_df.shape,
    )

    # Run prediction
    prediction_label = model.predict(features_df)[0]
    fraud_probability = _extract_probability(model, features_df)
    logger.info(
        "Prediction complete: label=%s probability=%.4f threshold=%.4f",
        prediction_label,
        fraud_probability,
        fraud_config.threshold,
    )
    is_fraud = bool(prediction_label == 1) or (
        fraud_probability >= fraud_config.threshold
    )

    result = FraudPrediction(
        is_fraud=is_fraud,
        fraud_probability=fraud_probability,
        model_name=fraud_config.model_name,
        reason=_build_reason(ctx, is_fraud, fraud_probability),
        model_version=_get_model_version(model),
    )

    if is_fraud:
        logger.warning(
            "Fraud detected: user=%s event=%s tier=%s qty=%d total=%.2f "
            "prob=%.4f model=%s",
            ctx.user_id,
            ctx.event_id,
            ctx.tier_category,
            ctx.quantity,
            ctx.total_price,
            fraud_probability,
            fraud_config.model_name,
        )
    else:
        logger.info(
            "Order cleared: user=%s event=%s prob=%.4f",
            ctx.user_id,
            ctx.event_id,
            fraud_probability,
        )

    return result


def _extract_probability(model, features_df) -> float:
    """Extract fraud probability from the model, handling various APIs."""
    try:
        proba = model.predict_proba(features_df)
        # Standard scikit-learn API: shape (n_samples, n_classes)
        # Class 1 (fraud) is typically the second column
        if proba.shape[1] >= 2:
            return float(proba[0, 1])
        return float(proba[0, 0])
    except AttributeError:
        # Model doesn't support predict_proba — fall back to decision_function
        try:
            decision = model.decision_function(features_df)
            # Sigmoid to approximate probability
            return float(1.0 / (1.0 + np.exp(-decision[0])))
        except AttributeError:
            # Raw predict only — use label as crude probability
            label = model.predict(features_df)[0]
            return 1.0 if label == 1 else 0.0


def _build_reason(
    ctx: OrderContext, is_fraud: bool, probability: float
) -> str:
    """Build a human-readable reason for the prediction."""
    if not is_fraud:
        return "Passed fraud check"
    parts = [f"Fraud probability {probability:.2%} exceeds threshold"]
    order_value_ratio = (
        ctx.total_price / ctx.user_avg_order_value
        if ctx.user_avg_order_value > 0 else 0.0
    )
    if order_value_ratio > 3.0:
        parts.append(
            f"Order value {ctx.total_price:.2f} is "
            f"{order_value_ratio:.1f}x average spend"
        )
    if ctx.quantity > 10:
        parts.append(f"Unusually high quantity: {ctx.quantity}")
    seat_occupancy_ratio = (
        ctx.tier_sold_quantity / ctx.tier_total_seats
        if ctx.tier_total_seats > 0 else 0.0
    )
    if seat_occupancy_ratio > 0.95:
        parts.append("Near-sold-out event (possible scalping)")
    return "; ".join(parts)

from typing import Optional
def _get_model_version(model) -> Optional[str]:
    """Try to extract a version string from the model object."""
    return getattr(model, "version", None) or getattr(
        model, "__version__", None
    )
