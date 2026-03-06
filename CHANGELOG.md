# Changelog

All notable changes to BetterMind CRM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - 2026-03-06

### Added

- **Contact Information Card** with clickable email (mailto:), phone (tel:), LinkedIn, website, Twitter/X, and Google Maps links
- **Inline edit mode** on the Contact Info Card with Save/Cancel controls
- **Delete contact** button with confirmation dialog
- **Copy to clipboard** for email and phone fields
- New contact fields: `address_line1`, `address_line2`, `city`, `state`, `zip`, `country`, `website`, `twitter_url`
- **Contact completeness indicator** in the list view (green/yellow/red dot)
- **Clickable contact icons** in the list view (email, phone, LinkedIn) that open directly without navigating to the detail panel
- **In-app Help button** that displays the full user manual in a modal
- `GET /api/help` endpoint serving user manual content
- Migration-safe schema evolution: `ALTER TABLE ADD COLUMN IF NOT EXISTS` for PostgreSQL, `try/except` for SQLite

### Changed

- Contact detail panel redesigned with structured layout: Header, Contact Info Card, Pipeline and Actions, Notes, Deals, Activity Log
- Empty contact info fields are hidden automatically
- Contact list refreshes automatically after edits

## [1.0.0] - 2026-03-05

### Added

- **Contact management** with categories (investor, Google, team, advisor, partner, vendor, university, media, other)
- **Organization directory** linking contacts to companies
- **Investor pipeline** with deal tracking, stages, amounts, and probability
- **Interaction logging** for emails, calls, meetings, and notes
- **Program tracking** with milestones and status
- **Tag system** for flexible contact categorization
- **Multi-user authentication** with role-based access (admin/user)
- **Dashboard statistics** with contact counts, active investors, deal counts, and interaction totals
- **Full REST API** with FastAPI and interactive Swagger docs at `/docs`
- **Search** across contact names, emails, titles, notes, and organization names
- **Status filtering** with clickable status pills
- **Category tabs** for quick filtering (All, Investors, Google, Team, Advisors)
- **Dual database support**: PostgreSQL (Cloud SQL) in production, SQLite for local development
- **HMAC token authentication** with stateless JWT-style tokens (7-day TTL)
- **PBKDF2 password hashing** with legacy SHA-256 fallback
- **Docker multi-stage build** (Node for frontend, Python for backend)
- **Cloud Run deployment** with `deploy.sh` script
- **Seed data** for demo contacts, organizations, interactions, and deals
- Mobile-responsive React frontend (single-file `App.jsx`)
- Vite dev server with API proxy for local development

## [Unreleased]

### Planned

- Split `main.py` into route modules
- Split `App.jsx` into React components
- Expanded test coverage
- GitHub Actions CI pipeline
