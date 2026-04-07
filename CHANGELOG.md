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

- Expanded test coverage
- GitHub Actions CI pipeline
- Screenshot gallery in README

## [1.2.0] - 2026-04-07

### Added

- **Dynamic category and subcategory management** — categories and subcategories are now stored in PostgreSQL tables instead of hardcoded enums
- New `categories` and `subcategories` database tables with icons, display names, and sort order
- **Category CRUD API** — `GET/POST/PUT/DELETE /api/categories` and `/api/subcategories`
- **Legislator category** with National (Federal) and State Legislature subcategories
- **Category/subcategory validation** against the database on contact create, update, and bulk update, with clear error messages listing valid values
- **Delete protection** — categories and subcategories cannot be deleted while contacts reference them
- Dynamic category/subcategory dropdowns in the Contact Detail edit mode
- Dynamic navigation tabs fetched from the categories API (including new Legislators tab)
- `seed_categories()` function for idempotent seeding of all categories and subcategories on startup
- `test_categories.ps1` — comprehensive non-destructive test suite (80+ assertions)

### Changed

- Removed hardcoded `VALID_CATEGORIES` from Pydantic models — validation now queries the database
- Dropped `contacts_category_check` PostgreSQL CHECK constraint in favor of database-driven validation
- Category icons in the frontend are now fetched from the API instead of a static `CAT_ICONS` map
- Navigation tabs are dynamically generated from the categories API response
- Bulk update endpoint (`PUT /api/bulk/contacts`) now validates category against the database

## [1.1.1] - 2026-03-07

### Security

- Fix path traversal vulnerability in static file serving
- Fix XSS in HelpModal markdown link href sanitization
- Shorten token TTL from 7 days to 24 hours
- Add password version claim to tokens for revocation on password change
- Add authentication to `/api/help` endpoint
- Add IP-based rate limiting to `/api/login` (10 attempts per 5 minutes)

### Changed

- Split `main.py` into modular route files (`routes/contacts.py`, `routes/organizations.py`, etc.)
- Split `App.jsx` into React components (`ContactDetail.jsx`, `HelpModal.jsx`, `LoginScreen.jsx`, `UserManagement.jsx`, `ui.jsx`)
- Extract shared database helpers into `deps.py`
- Extract auth logic into `auth.py`
- Extract Pydantic models into `models.py`
- Harden SQL column allowlists with `frozenset` in all route files
- Standardize INSERT parameter naming from positional to descriptive names
- Add category and status validators to Contact models
- Extract shared email validator function in models
- Auto-commit in `db()` context manager on clean exit
- Enable SQLite FK enforcement
- Rename private hash/verify functions to public names
- Fix `UserManagement` error messages always showing green
- Fix array index keys in `ContactDetail` mapped lists
- Wrap `UserManagement` loadUsers in `useCallback`
- Use label as key for stats header in `App.jsx`
- Add `cursor:pointer` to Pill component
- Remove unreferenced Instrument Sans font
- Set `package.json` `private: true`
- Fix `cloudbuild.yaml` to pass env vars and Cloud SQL config
- Fix `docker-compose` volume mount path
- Add `requirements-dev.txt` for test dependencies
- Remove all em dashes from copy
- Update all repo URLs to `Investor-CRM`

### Added

- `DATABASE_URL` env var support for direct PostgreSQL connections (local Docker dev)
- `.env.example` with placeholder credentials
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `LICENSE` (MIT)
- GitHub issue templates and PR template
- `docs/API_REFERENCE.md` and `docs/DEPLOYMENT.md`
- Professional README for open source / YC audience
