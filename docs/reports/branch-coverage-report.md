# Branch Coverage Report

**Project:** Healthcare Appointment & Patient Record System · **Team:** 13 · **Generated:** 12-11-2026 14:54

Branch coverage (every `if`/`else`, loop and early-return path taken both ways) measured with `pytest --cov-branch`. A *partial* branch was taken only one way.

| Metric | Value |
|---|---|
| Branches | 316 |
| Covered | 287 |
| Partial | 27 |
| **Branch coverage** | **90.8%** |

## Per module

| Module | Branches | Partial | Coverage |
|---|---|---|---|
| `app/core/config.py` | 2 | 1 | 50.0% |
| `app/core/crypto.py` | 10 | 0 | 100.0% |
| `app/core/database.py` | 8 | 2 | 75.0% |
| `app/core/events.py` | 4 | 1 | 75.0% |
| `app/core/scheduler.py` | 8 | 1 | 87.5% |
| `app/core/security.py` | 6 | 0 | 100.0% |
| `app/main.py` | 14 | 1 | 78.6% |
| `app/services/appointments/router.py` | 36 | 0 | 100.0% |
| `app/services/appointments/service.py` | 30 | 4 | 86.7% |
| `app/services/audit/router.py` | 6 | 1 | 83.3% |
| `app/services/auth/router.py` | 10 | 3 | 70.0% |
| `app/services/auth/schemas.py` | 6 | 0 | 100.0% |
| `app/services/auth/service.py` | 14 | 1 | 92.9% |
| `app/services/doctors/router.py` | 12 | 0 | 100.0% |
| `app/services/doctors/schemas.py` | 2 | 0 | 100.0% |
| `app/services/doctors/service.py` | 36 | 1 | 97.2% |
| `app/services/jobs/plugin.py` | 4 | 1 | 75.0% |
| `app/services/notifications/mailer.py` | 6 | 0 | 100.0% |
| `app/services/notifications/reports.py` | 6 | 0 | 100.0% |
| `app/services/notifications/router.py` | 8 | 0 | 100.0% |
| `app/services/notifications/service.py` | 6 | 0 | 100.0% |
| `app/services/patients/router.py` | 20 | 4 | 80.0% |
| `app/services/patients/schemas.py` | 2 | 0 | 100.0% |
| `app/services/patients/service.py` | 6 | 0 | 100.0% |
| `app/services/records/access.py` | 8 | 2 | 75.0% |
| `app/services/records/chart.py` | 4 | 0 | 100.0% |
| `app/services/records/consultations.py` | 12 | 1 | 91.7% |
| `app/services/records/pdf.py` | 2 | 0 | 100.0% |
| `app/services/records/prescriptions.py` | 8 | 1 | 87.5% |
| `app/services/records/schemas_clinical.py` | 2 | 0 | 100.0% |
| `app/services/security/middleware.py` | 12 | 2 | 83.3% |
| `src/scheduling.py` | 6 | 0 | 100.0% |
