# Shapater CRM

Multi-tenant, white-label Real Estate CRM for Pakistan + Gulf agencies, with **automatic property ↔ client-requirement matching**.

## Run
```bash
docker compose up --build   # API http://localhost:8000/docs  |  Dashboard http://localhost:3000
```
Sign up on the login page (creates your agency), then: **Paste a message** → **Matches**.

### Develop
```bash
cd backend && pip install -r requirements-dev.txt && pytest -q
```

## What is built (v0.1)
- Multi-tenant auth (agency signup, JWT, roles: owner / manager / agent)
- Properties, Clients (duplicate detection by normalised phone), Requirements
- **Matching engine**: score 0-100 with explainable breakdown (budget, location, type, bedrooms, features); runs automatically when a property/requirement is created or edited
- Leads pipeline + activities/follow-up reminders, dashboard summary
- WhatsApp share message + `wa.me` link per match
- Multi-currency (PKR/AED/SAR/USD…), marla/kanal/sqft/sqm conversion, RERA/Trakheesi permit field
- Soft delete, audit log
- **PostgreSQL Row-Level Security** (DB-enforced tenant isolation, fail-closed) + Alembic migrations
- CSV import (clients, properties) and WhatsApp message parser (`POST /api/v1/ai/parse-message`)

- **Roles & permissions**: owner / manager see the whole agency; **agents see only clients, leads and matches assigned to them**. Team page to add members and assign clients
- **Login brute-force protection** (5 failed attempts / 15 min, `Retry-After`)
- **Integrations & keys** (owner-only): add/edit/delete/copy Stripe, WhatsApp, AI keys. Encrypted at rest (Fernet, rotation-ready), masked in lists, reveal/copy audited, RLS-isolated per agency
- **Dashboard (Next.js)**: overview, matches with the Fit Gauge, properties, clients + requirements, drag-and-drop pipeline, paste-a-message, CSV import

## Deploy
See [DEPLOY.md](DEPLOY.md) (Render + Vercel, free for testing).

## Security notes
- Set `SECRET_KEY` and `ENCRYPTION_KEYS` before production (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`). Losing `ENCRYPTION_KEYS` makes stored keys unreadable, so back it up in a secrets manager.
- Never commit real keys. `.env` is git-ignored.

## Roadmap
1. Urdu/Arabic i18n (RTL), live FX rates
2. Celery/Redis background jobs, WhatsApp Cloud API (send + inbound)
3. LLM-based message parser, brochure PDF, public listing pages
4. Billing (Stripe), white-label branding/domains, super-admin
5. 2FA, change-password / password reset, Redis-backed rate limiting
