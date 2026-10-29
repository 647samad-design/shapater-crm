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

# No credit card? Use Neon + Hugging Face + Vercel (all free, no card)

| Part | Where |
|---|---|
| Database | **Neon** (free Postgres) |
| API | **Hugging Face Spaces** (free Docker Space) |
| Dashboard | **Vercel** |

Free-tier notes: a Hugging Face Space sleeps after about 48 hours without traffic (first request then takes ~30 s); its disk is wiped on restart, so data must live in Neon (it does). Neon's free plan has storage and compute-hour limits. Test data only.

## 1. Database on Neon
1. neon.com → sign up with GitHub → **Create project** (name `shapater`, Postgres 16, region Singapore or closest).
2. Click **Connect**. **Turn OFF "Connection pooling"** (the pooled URL breaks this app), copy the connection string (starts with `postgresql://...`). This is your `DATABASE_URL`.

## 2. API on Hugging Face
1. huggingface.co → sign up (no card) → **New Space** → name `shapater-api`, SDK **Docker → Blank**, hardware **CPU basic (free)**, visibility **Public**.
2. In the Space → **Files → Add file → Upload files**: upload the two files from `deploy/huggingface/` in this repo (`Dockerfile`, `README.md`). Commit.
3. Space → **Settings → Variables and secrets → New secret**, add four secrets:
   - `DATABASE_URL` = the Neon string
   - `SECRET_KEY` = any long random string
   - `ENCRYPTION_KEYS` = another long random string (save it)
   - `CORS_ORIGINS` = `["https://YOUR-APP.vercel.app"]`
4. Wait for **Building → Running**. Your API URL is `https://YOUR-USERNAME-shapater-api.hf.space`. Open `/health` on it: `{"status":"ok"}`.
5. To deploy new code later: Settings → **Factory rebuild**.

## 3. Dashboard on Vercel
Same as before: import the repo as a single project with Root Directory `frontend`, and set `NEXT_PUBLIC_API_URL` to the `.hf.space` URL. Then update `CORS_ORIGINS` on Hugging Face with the real Vercel URL (Space restarts automatically).
