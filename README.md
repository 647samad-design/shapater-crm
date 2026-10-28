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

- **Dashboard (Next.js)**: overview, matches with the Fit Gauge, properties, clients + requirements, drag-and-drop pipeline, paste-a-message, CSV import

## Roadmap
1. Urdu/Arabic i18n (RTL), live FX rates
2. Celery/Redis background jobs, WhatsApp Cloud API (send + inbound)
3. LLM-based message parser, brochure PDF, public listing pages
4. Billing (Stripe), white-label branding/domains, super-admin
5. Per-agent permissions (agents see only their leads), 2FA, rate limiting
