# Event-Ticketing-Platform-with-Fraud-Detection

A production-grade event ticketing system with real-time seat reservation, secure payments, QR-based check-in, and fraud detection.

# Features
Event & venue management (seat maps / general admission)
Real-time seat locking to prevent overselling
Secure checkout via Stripe (test mode)
QR-code ticket generation & check-in scanning
Order history, refunds, and ticket transfers
Fraud/anomaly detection on suspicious purchases
# Tech Stack
Backend: FastAPI, PostgreSQL, Redis, Celery
Frontend: Fill up according to your tech stack
Fraud Detection Model : Full up according to your tech stack
Payment system: Not our Goal for now
Infrastructure: Docker & Docker Compose (If anyone know more about Deployment they can add some more points)
# Architecture Overview
Client browses events → selects seats → temporary hold placed in Redis
Checkout triggers Stripe Payment Intent
On payment success , seat status confirmed in Postgres
Ticket issued with unique QR code
Check-in scans QR → validates against Postgres → marks ticket used