# Deploy for testing (free)

Dashboard on **Vercel**, API + database on **Render**. Total cost: $0 for a test.

## Know the free-tier limits (checked Oct 2026, verify on the providers' pages)
- Render free web service **sleeps after 15 min idle**; the first request then takes about a minute.
- Render free Postgres **expires 30 days after creation** (14-day grace to upgrade). Fine for testing, never for real customers' data.
- Do not put real client data in a test deployment.

## 1. Generate your secrets (on your computer)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Keep the output: it is your `ENCRYPTION_KEYS`. (No Python? Any long random string also works, e.g. Render's "Generate" button.) If you lose it, saved API keys cannot be read again.

## 2. API + database on Render
1. render.com → **New → Blueprint** → connect the `shapater-crm` GitHub repo (it finds `render.yaml`).
2. When asked, fill in:
   - `ENCRYPTION_KEYS` = the key from step 1
   - `CORS_ORIGINS` = `["https://YOUR-APP.vercel.app"]` (you can edit it after step 3)
3. Deploy. When it is live, open `https://YOUR-API.onrender.com/health`: it should show `{"status":"ok"}`. API docs are at `/docs`.

## 3. Dashboard on Vercel
1. vercel.com → **Add New → Project** → import the same repo.
2. **Root Directory:** `frontend`. Framework: Next.js (auto).
3. **Environment variable:** `NEXT_PUBLIC_API_URL` = `https://YOUR-API.onrender.com`
4. Deploy, then put the Vercel URL into `CORS_ORIGINS` on Render and redeploy the API.

## 4. Try it
Open the Vercel URL → create your agency → Paste a message → Matches.

## Going to real customers later
Paid always-on API (about $7/month), paid Postgres with backups, your own domain, and a rotated `SECRET_KEY`. Also revoke any tokens that were ever pasted into chats.

---

# No credit card? Use Neon + Vercel (both free, no card)

Render needs a card for verification and Hugging Face Docker Spaces are now paid, so for a card-free test use:

| Part | Where |
|---|---|
| Database | **Neon** (free Postgres) |
| API | **Vercel** (project 1, Root Directory `backend`) |
| Dashboard | **Vercel** (project 2, Root Directory `frontend`) |

Notes: the API runs as a serverless function, so the first request after idle can take a few seconds (Vercel cold start + Neon waking up). Test data only. Verify current free-plan limits on both sites.

## 1. Database on Neon
1. neon.com → create project `shapater` → **Connect** → turn **OFF "Connection pooling"** → copy the connection string. This is `DATABASE_URL`.
2. Open **SQL Editor** in Neon, paste the full contents of [`deploy/schema.sql`](deploy/schema.sql), and click **Run**. This creates all tables (Vercel cannot run migrations).

## 2. API on Vercel (project 1)
1. vercel.com → **Add New → Project** → import this repo → click **Import single project** on the **backend** line.
2. Check: **Root Directory = `backend`**, Framework = FastAPI/Python. (`backend/index.py` is the entrypoint Vercel looks for.)
3. Environment variables:
   - `DATABASE_URL` = Neon string
   - `SECRET_KEY` = a long random string
   - `ENCRYPTION_KEYS` = another long random string (save it)
   - `CORS_ORIGINS` = `["https://YOUR-DASHBOARD.vercel.app"]` (update after step 3)
4. Deploy. Open `https://YOUR-API.vercel.app/health` → `{"status":"ok"}`.

## 3. Dashboard on Vercel (project 2)
Import the same repo again → **Import single project** on the **frontend** line → Root Directory `frontend` → env `NEXT_PUBLIC_API_URL` = the API URL from step 2 → Deploy. Then put the dashboard URL into the API project's `CORS_ORIGINS` and **Redeploy** the API.

## Changing the database later
Add a new Alembic migration, then regenerate SQL with `alembic upgrade head --sql` (or run only the new part) and run it in Neon's SQL Editor.
