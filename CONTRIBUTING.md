# Contributing to BetterMind CRM

Thanks for your interest in contributing! This project is open source and we welcome bug reports, feature suggestions, and pull requests from the community.

## Reporting Bugs

Open a [GitHub Issue](https://github.com/jessl2juice/bettermind-crm/issues/new?template=bug_report.md) with:

- **Steps to reproduce** the problem
- **Expected behavior** vs. what actually happened
- **Environment** (OS, browser, Python version, Node version)
- **Screenshots** if applicable

## Suggesting Features

Open a [Feature Request](https://github.com/jessl2juice/bettermind-crm/issues/new?template=feature_request.md) with:

- **Problem** you're trying to solve
- **Proposed solution** (even if rough)
- **Alternatives** you've considered

## Submitting Pull Requests

1. Fork the repo and create your branch from `main`.
2. Set up local development (see below).
3. Make your changes. Keep PRs focused on a single concern.
4. Add or update tests if you changed backend behavior.
5. Make sure the app builds and tests pass.
6. Open a PR with a clear description of what changed and why.

### PR Checklist

- [ ] Backend tests pass (`cd backend && python -m pytest`)
- [ ] Frontend builds cleanly (`cd frontend && npm run build`)
- [ ] No hardcoded credentials or secrets
- [ ] Documentation updated if you changed API endpoints or UI behavior

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The backend starts at `http://localhost:8080` with SQLite (no database setup needed).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server starts at `http://localhost:5173` and proxies `/api` requests to the backend.

### Docker

```bash
docker-compose up
# App available at http://localhost:8080
```

## Code Style

### Python (Backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for function signatures
- Keep functions focused and under ~50 lines where practical
- Use `sqlalchemy.text()` for all SQL queries (no ORM)

### JavaScript (Frontend)

- Follow ESLint defaults
- Use functional React components with hooks
- Inline styles are fine (the project uses inline styles throughout)
- Keep component logic self-contained

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Questions?

Open a [Discussion](https://github.com/jessl2juice/bettermind-crm/discussions) or file an issue. We're happy to help.
