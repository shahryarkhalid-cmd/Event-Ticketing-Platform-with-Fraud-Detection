# Event Ticketing Platform

A production-grade event ticketing system with real-time seat reservation, secure payments, QR-based check-in, and fraud detection.

## Features
- Event & venue management (seat maps / general admission)
- Real-time seat locking to prevent overselling
- Secure checkout via Stripe (test mode)
- QR-code ticket generation & check-in scanning
- Order history, refunds, and ticket transfers
- Fraud/anomaly detection on suspicious purchases

## Tech Stack
- **Backend:** FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** Fill up according to your tech stack
- **Fraud Detection Model:** Python, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, MLflow, Pickle, Python Logging,Jupyter Notebook.
- **Payment System:** Not our goal for now
- **Infrastructure:** Docker & Docker Compose (add deployment details if anyone knows more)

## Architecture Overview
1. Client browses events → selects seats → temporary hold placed in Redis
2. Checkout triggers Stripe Payment Intent
3. On payment success, seat status confirmed in Postgres
4. Ticket issued with unique QR code
5. Check-in scans QR → validates against Postgres → marks ticket used
