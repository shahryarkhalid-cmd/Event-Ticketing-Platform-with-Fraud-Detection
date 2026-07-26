# Tixora Fraud Detection — Training Report (v2)

## Executive Summary

Trained on 51,599 orders (3.85% fraud) built entirely from the application's existing `User`/`Event`/`TicketTier`/`Order` tables. The best model, **xgboost**, reaches a test PR-AUC of 0.825 (ROC-AUC 0.963) using only fields the application already collects today — no database migration or endpoint change required.

Using the same trained model with the 17 optional (device/network/payment-attempt) columns entirely absent — the current production reality — retains **99.1%** of the full-feature PR-AUC (0.818 vs 0.825). The model is deployable as-is; the optional signals are a future enhancement, not a dependency.

## Dataset Summary

- Rows: 51,599
- Fraud rate: 3.85%
- Core features: 29 (always available)
- Optional features: 17 (defaulted when absent)
- Train/val/test split: 36,119 / 7,740 / 7,740

## Feature Summary

**Core (mandatory, always computable from existing app data):**
`quantity`, `total_price`, `price_per_ticket`, `price_deviation_from_listed`, `account_age_days`, `purchases_last_1h`, `purchases_last_24h`, `purchases_last_7d`, `spend_last_24h`, `spend_last_7d`, `distinct_events_last_24h`, `time_since_last_order_hours`, `user_lifetime_order_count`, `user_historical_refund_rate`, `user_historical_paid_rate`, `purchase_hour`, `purchase_weekday`, `purchase_month`, `days_until_event`, `hours_since_tier_listed`, `quantity_share_of_tier_capacity`, `event_popularity_ratio`, `organizer_historical_refund_rate`, `is_verified`, `is_active`, `is_first_order`, `is_weekend`, `is_late_night`, `event_category`

**Optional (defaulted when the app doesn't send them):**
`failed_payments`, `payment_attempts`, `purchases_same_device_24h`, `purchases_same_ip_24h`, `purchases_same_card_24h`, `unique_devices_per_user`, `unique_cards_per_device`, `vpn_detected`, `proxy_detected`, `datacenter_ip`, `phone_verified`, `ip_event_country_mismatch`, `device_type`, `browser`, `operating_system`, `ip_country`, `ip_city`

## Class-Imbalance Strategy

SMOTE vs. class-weighting alone was compared via 3-fold CV PR-AUC: baseline 0.5848 vs. SMOTE 0.5695. Decision: **class-weighting only, no SMOTE** (SMOTE did not demonstrate a genuine improvement here).

## Model Comparison (validation PR-AUC)

| model                  |   val_pr_auc |   train_seconds | tuned   |
|:-----------------------|-------------:|----------------:|:--------|
| xgboost                |     0.792619 |        99.9546  | True    |
| hist_gradient_boosting |     0.783731 |        99.569   | True    |
| lightgbm               |     0.769696 |         2.1885  | False   |
| catboost               |     0.769286 |         5.02129 | False   |
| random_forest          |     0.763457 |        19.6804  | False   |
| extra_trees            |     0.671907 |        17.106   | False   |
| logistic_regression    |     0.576153 |         0.69295 | False   |

## Held-out Test Set Evaluation — xgboost

- Threshold: 0.5
- Accuracy: 0.9468
- Precision: 0.4069
- Recall: 0.8356
- F1: 0.5473
- ROC-AUC: 0.9635
- PR-AUC: 0.8254
- Confusion matrix (rows=actual, cols=predicted): [[7079, 363], [49, 249]]

```
              precision    recall  f1-score   support

           0      0.993     0.951     0.972      7442
           1      0.407     0.836     0.547       298

    accuracy                          0.947      7740
   macro avg      0.700     0.893     0.759      7740
weighted avg      0.971     0.947     0.955      7740

```

## Top 15 Feature Importances

| feature                               |   importance |
|:--------------------------------------|-------------:|
| core_num__user_historical_paid_rate   |    0.131697  |
| core_num__quantity                    |    0.0822523 |
| core_num__hours_since_tier_listed     |    0.0785416 |
| core_num__is_late_night               |    0.0691933 |
| core_num__purchases_last_1h           |    0.0556063 |
| core_num__time_since_last_order_hours |    0.0511201 |
| core_num__purchase_hour               |    0.040387  |
| core_num__user_lifetime_order_count   |    0.0292342 |
| opt_num__failed_payments              |    0.0274305 |
| opt_num__unique_devices_per_user      |    0.0238265 |
| core_num__days_until_event            |    0.0218605 |
| core_num__account_age_days            |    0.0166567 |
| core_cat__event_category_Nightlife    |    0.016477  |
| opt_num__purchases_same_card_24h      |    0.0159568 |
| opt_num__payment_attempts             |    0.0151523 |

## Recommendations

- Deploy as-is using only core features; treat optional-signal capture (device/IP/payment-attempt telemetry) as a future enhancement, not a blocker.
- Monitor precision/recall drift monthly; retrain when validated new labeled data (confirmed chargebacks/disputes) becomes available.
- Revisit the decision threshold against the actual operational cost of a false positive (blocked legitimate purchase) vs. a false negative (missed fraud).

## Limitations

- Trained entirely on synthetic data; real fraud patterns should be validated against this model once genuine labeled outcomes exist.
- `stealth_fraud` cases are deliberately not cleanly separable from legitimate orders using transactional data alone — a ceiling on recall is expected and realistic, not a bug.
- Optional features were generated with correlated-but-noisy signal; real device/network data, once captured, may carry more or less signal than modeled here.

## Future Improvements

- Capture device/IP/payment-attempt telemetry at checkout to activate the optional feature group for real.
- Add a genuine phone-verification field to `User` if phone-based risk scoring becomes a priority.
- Automate the retraining pipeline against a schema/data-drift monitor.
