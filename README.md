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
