# Tixora Fraud Detection — Training Schema (v2)

This schema is built **only** from fields that already exist in the live application
(`User`, `Event`, `TicketTier`, `Order`). No database migration, endpoint change, or
frontend change is required to eventually populate this schema from production data.

Per your instruction, IP address / device fingerprint / geolocation are **not** part of
this schema. They are represented as reserved, nullable placeholder columns so the
pipeline can accept them later with zero redesign — see "Forward-compatibility hooks"
at the bottom.

## Source tables (normalized, mirrors the real DB)

### `users.csv` — from `app/models/Users.py::User`
| column | type | source |
|---|---|---|
| `user_id` | int | `User.id` |
| `role` | category (`customer`/`organizer`) | `User.role` |
| `is_active` | bool | `User.is_active` |
| `is_verified` | bool | `User.is_verified` |
| `account_created_at` | datetime | `User.created_at` |

`email`/`full_name`/`hashed_password` are excluded — direct identifiers, no
fraud signal, and out of scope to carry into a training set.

### `events.csv` — from `app/models/Event.py::Event`
| column | type | source |
|---|---|---|
| `event_id` | int | `Event.id` |
| `organizer_id` | int | `Event.organizer_id` |
| `category` | category | `Event.category` |
| `city`, `country` | string | `Event.city`, `Event.country` |
| `max_capacity` | int | `Event.max_capacity` |
| `listed_at` | datetime | `Event.created_at` (when tickets went on sale) |
| `start_datetime`, `end_datetime` | datetime | `Event.start_datetime/end_datetime` |

### `ticket_tiers.csv` — from `app/models/Ticket.py::TicketTier`
| column | type | source |
|---|---|---|
| `tier_id` | int | `TicketTier.id` |
| `event_id` | int | `TicketTier.event_id` |
| `category_name` | string | `TicketTier.category_name` |
| `price` | float | `TicketTier.price` |
| `total_seats` | int | `TicketTier.total_seats` |

`sold_quantity` is mutable running state on the live table, not a historical fact —
the training pipeline reconstructs "seats sold before this order" from prior `Order`
rows instead of trusting a point-in-time counter (avoids leakage from future sales).

### `orders.csv` — from `app/models/Orders.py::Order` (**the transaction table**)
| column | type | source |
|---|---|---|
| `order_id` | int | `Order.id` |
| `user_id` | int | `Order.user_id` |
| `event_id` | int | `Order.event_id` |
| `tier_id` | int | `Order.ticket_tier_id` |
| `quantity` | int | `Order.quantity` |
| `total_price` | float | `Order.total_price` |
| `status` | category (`pending`/`paid`/`refunded`) | `Order.status` |
| `created_at` | datetime | `Order.created_at` |
| `has_qr_code` | bool | `Order.qr_code is not None` |
| `is_fraud` | bool (**target**) | synthetic label — not a real column, see note below |
| `fraud_type` | category (debug only) | synthetic metadata — **must be dropped before training**, kept only for EDA/audit |

> **`is_fraud` does not exist in the live app.** No chargeback/dispute tracking or
> fraud flag is stored anywhere today. The synthetic dataset invents this label so
> the model has something to learn from; in production the model would *produce*
> a fraud score, not consume one from the DB.

## Engineered features (computed from the tables above only)
Grouped so each group can be toggled independently in the notebook:

- **Amount**: `total_price`, `price_per_ticket`, `log1p(total_price)`, deviation of
  `price_per_ticket` from the tier's listed `price`
- **Quantity**: `quantity`, `quantity / tier.total_seats` (bulk-share of a tier)
- **Timing**: hour-of-day, day-of-week, `is_late_night`, `days_until_event`,
  `hours_since_tier_listed`
- **Account**: `account_age_days` at order time, `is_verified`, `is_active`
- **Velocity** (rolling, computed from prior `Order` rows for the same `user_id`):
  order count / spend in the last 1h / 24h / 7d, distinct events/tiers touched in 24h,
  time-since-previous-order
- **Behavioral history**: user's lifetime order count, historical refund rate,
  historical paid-rate, "is this the user's first-ever order"
- **Merchant/event context**: organizer's historical refund rate across their events,
  event category, event popularity (seats sold / max_capacity so far)

All of these are reproducible today from `Order` + `User` + `Event` + `TicketTier`
history alone — no new capture required.

## Forward-compatibility hooks (not populated now, wired for later)
`orders.csv` includes three reserved columns, generated as all-null in this dataset:

- `ip_address`, `user_agent`, `device_id`

The feature-engineering module treats each feature group as a pluggable unit; the
"network" group is registered but currently a no-op (returns nothing because the
columns are null). When these columns are eventually populated from real requests,
the network feature group activates automatically — no changes needed to the rest
of the pipeline, the model interface, or the other feature groups.
