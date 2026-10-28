# Shapater CRM

Multi-tenant, white-label Real Estate CRM for Pakistan + Gulf agencies, with **automatic property ↔ client-requirement matching**.

## Run
```bash
docker compose up --build        # API on http://localhost:8000/docs
# or locally
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

## Roadmap
1. Alembic migrations + PostgreSQL Row-Level Security
2. Next.js dashboard (Kanban, matches, analytics) + Urdu/Arabic i18n
3. CSV import, Celery/Redis background jobs, WhatsApp Cloud API
4. AI WhatsApp-message parser, brochure PDF, public listing pages
5. Billing (Stripe), white-label branding/domains, super-admin
