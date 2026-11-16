# Healthcare Appointment & Patient Record System

Software Engineering Mini Project – Team 13, PES University

## Problem statement

Manage patients, doctors, appointments, medical histories and prescriptions securely. Enforce role-based access and prevent appointment conflicts.

## Team

| Name | SRN | GitHub |
|---|---|---|
| P Manas Siddhardha (lead) | PES1UG24AM186 | [siddhardha-06](https://github.com/siddhardha-06) |
| Prithviraj K | PES1UG24AM204 | [Prithviraj-techie](https://github.com/Prithviraj-techie) |
| Parth Kale | PES1UG24AM184 | [Parthkale64](https://github.com/Parthkale64) |
| Raghav Budur (colead) | PES1UG23AM225 | [RAGHAV-BUDUR](https://github.com/RAGHAV-BUDUR) |

## Users

- **Patient** – registers, books / reschedules / cancels appointments, views own history and prescriptions
- **Doctor** – sets availability and leave, sees the daily schedule, writes consultation notes and prescriptions
- **Receptionist** – registers walk-in patients, books on behalf of patients, checks patients in
- **Admin** – manages staff accounts and doctor profiles, views the dashboard, exports reports

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React (web, mobile-responsive) |
| Backend | Python FastAPI (REST, JSON), SQLAlchemy ORM |
| Database | PostgreSQL 15 |
| Auth | JWT bearer tokens (30-minute expiry), bcrypt password hashing (cost 12) |
| Encryption | TLS 1.2+ in transit; AES-256-GCM for sensitive medical fields at rest |
| Background jobs | APScheduler (24-hour reminders, automatic No-show marking) |
| Email | SMTP (MailHog in testing) |
| PDF | ReportLab (prescription PDFs) |
| Tools | GitHub, PlantUML, Swagger, Postman, Pytest, Playwright, Locust, OWASP ZAP |

Appointment conflicts are prevented inside one database transaction (row lock on the slot, overlap check for the patient) and by a partial unique index on active appointments per slot.

## Run it

```
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python scripts/seed_demo.py --reset   # demo accounts, password Demo@1234 (admin: admin@hap.local / Admin@1234)
uvicorn app.main:create_app --factory --reload
```

Open http://localhost:8000 for the web app and http://localhost:8000/docs for the API (Swagger).

Settings (environment variables): `DATABASE_URL` (default SQLite `./hap.db`; PostgreSQL in production),
`JWT_SECRET`, `HAP_DATA_KEY` (base64 32-byte AES key), `SMTP_HOST`/`SMTP_PORT`, `ENABLE_SCHEDULER=1`,
`FORCE_HTTPS=1`, `ADMIN_EMAIL`/`ADMIN_PASSWORD`.

## Tests and reports

```
pytest --cov=app --cov=src --cov-branch --cov-report=json:reports/coverage.json --junitxml=reports/junit.xml
python scripts/generate_reports.py reports docs/reports
```

Every pull request runs the tests (coverage must stay ≥ 70 %) and the docs check in GitHub Actions; every merge to `main`
also builds the SRS, SAD and Test Plan documents. Performance (TC-PERF-01): `tests/perf/` (seed, quick load test, Locust file).

## Backlog and sprints

- Backlog: `docs/backlog/backlog.md` (created on GitHub with `python scripts/create_backlog.py`)
- Sprint reports, deviations and video scripts: `docs/sprints/`
- Test reports: `docs/reports/`

## Code layout

```
app/
  core/            config, database, errors, security (JWT, bcrypt, roles), events, scheduler, crypto
  services/<name>/ one package per component (auth, patients, doctors, appointments, records, audit,
                   notifications, jobs, security); each has plugin.py and is discovered automatically
frontend/          React UI (no build step): app.js shell + one file per page in pages/
tests/             pytest suites (one per service), tests/perf for load testing
scripts/           backlog, demo data, reports, docs check and docs build
```

## Repository layout

```
docs/
  requirements-registry.md   fixed IDs for all requirements and test cases
  srs/                       Software Requirements Specification sections
  sad/                       Software Architecture & Design sections
  testplan/                  Test Plan sections
    test-cases/              one file per test case
  diagrams/                  PlantUML sources (.puml) and exported PNGs
  final/                     assembled .docx deliverables
```

## Workflow

Every section is its own file and its own commit. Work happens on `docs/<document>-<name>` branches and reaches `main` only through a reviewed Pull Request merged with **Rebase and merge**.
