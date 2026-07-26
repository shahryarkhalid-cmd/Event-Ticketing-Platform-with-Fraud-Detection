# Event Ticketing Platform — Setup & Testing Guide

This guide walks you through setting up the project locally, so you can run the backend, test API routes, and connect the frontend.

---

## 1. Clone the repo

```bash
git clone https://github.com/shahryarkhalid-cmd/Event-Ticketing-Platform-with-Fraud-Detection.git
cd Event-Ticketing-Platform-with-Fraud-Detection
```

---

## 2. Set up Python virtual environment

```bash
python -m venv venv
```

**Activate it (Windows PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

If you get a permissions error:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating again.

You should see `(venv)` appear at the start of your terminal line — that confirms it's active.

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Set up your `.env` file

Copy `.env.example` to a new file named `.env` in the project root:

```bash
copy .env.example .env
```

Then fill in the real values. **Ask Shahryar privately (WhatsApp/Discord) for the real values** — never commit `.env` to Git.

```env
DATABASE_URL=<ask for the real Supabase connection string>
SECRET_KEY=<ask for the shared secret key>
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=<ask if testing payments>
STRIPE_PUBLISHABLE_KEY=<ask if testing payments>
```

---

## 5. Install Docker Desktop (needed for Redis)

Redis is used to prevent overselling tickets when multiple people book at the same time.

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install it and make sure it's running (you'll see a whale icon in your system tray/menu bar)

### First-time Redis setup (only once):
```bash
docker run -d --name redis-ticketing -p 6379:6379 redis:7
```

### Every time after that, just start it:
```bash
docker start redis-ticketing
```

### To stop it when you're done:
```bash
docker stop redis-ticketing
```

### Quick check it's running:
```bash
docker ps
```
You should see `redis-ticketing` listed with status `Up`.

---

## 6. Apply database migrations

The database schema is already set up on Supabase, but if you pull new changes that include migrations, run:

```bash
alembic upgrade head
```

---

## 7. Run the backend

```bash
uvicorn app.main:app --reload
```

Confirm it's working by opening:
```
http://localhost:8000/docs
```
This is Swagger UI — an interactive page where you can test every API route directly, without needing the frontend.

---

## 8. Run the frontend

Open a **new terminal** (keep the backend running in the other one), then:

```bash
cd frontend
python -m http.server 3000
```

Open your browser to:
```
http://localhost:3000/login_sign_in/login.html
```

---

## 9. Testing the app end-to-end

1. **Sign up** a new account (choose role: customer or organizer)
2. **Log in** — should redirect you to the dashboard (organizers) automatically
3. **As an organizer:** create an event with ticket categories, view it in "My Events," check Analytics/Revenue/Bookings pages
4. **As a customer:** browse events, book a ticket

### Testing via Swagger instead of the UI
Go to `http://localhost:8000/docs`, click the **Authorize** button, log in with your test account, and you can test any route directly with real requests — useful for checking backend behavior without going through the UI.

---

## 10. Running backend tests

```bash
pytest app/test_.py -v
```
This runs the full automated test suite — auth, events, bookings, concurrency handling, etc.

---

## Common issues

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Make sure your venv is activated and `pip install -r requirements.txt` ran successfully |
| `DATABASE_URL` errors | Double-check your `.env` file has the real Supabase connection string, no typos |
| Redis connection errors | Make sure Docker Desktop is running and `docker start redis-ticketing` was run |
| Frontend shows no data / errors in console | Make sure the backend is running on port 8000, and you're logged in (check `localStorage` has a token) |
| CORS errors in browser console | Make sure you're accessing the frontend via `http://localhost:3000/...`, not by double-clicking the HTML file directly |

---

## Notes

- Never commit your real `.env` file — only `.env.example` (with placeholder values) goes to GitHub
- Redis data is temporary/local — nothing to worry about losing
- The database (Supabase) is shared across the team — be mindful when testing destructive actions (deleting events, etc.)
