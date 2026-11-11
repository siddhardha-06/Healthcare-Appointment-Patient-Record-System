# Code Coverage Report

**Project:** Healthcare Appointment & Patient Record System · **Team:** 13 · **Generated:** 29-10-2026 17:51

Statement (line) coverage of the application code (`app/`, `src/`) measured with coverage.py while the full pytest suite runs. Target from HAP-NF-005: **≥ 70 %** of the service layer; the CI job fails below 70 %.

| Metric | Value |
|---|---|
| Statements | 1893 |
| Covered | 1861 |
| Missed | 32 |
| **Line coverage** | **98.3%** |
| Target met (≥ 70 %) | Yes |

## Per module

| Module | Statements | Missed | Coverage |
|---|---|---|---|
| `app/core/clock.py` | 6 | 0 | 100.0% |
| `app/core/config.py` | 28 | 1 | 96.4% |
| `app/core/crypto.py` | 28 | 0 | 100.0% |
| `app/core/database.py` | 35 | 1 | 97.1% |
| `app/core/errors.py` | 36 | 2 | 94.4% |
| `app/core/events.py` | 14 | 0 | 100.0% |
| `app/core/roles.py` | 6 | 0 | 100.0% |
| `app/core/scheduler.py` | 44 | 3 | 93.2% |
| `app/core/schemas.py` | 7 | 0 | 100.0% |
| `app/core/security.py` | 47 | 0 | 100.0% |
| `app/main.py` | 46 | 3 | 93.5% |
| `app/services/appointments/models.py` | 28 | 0 | 100.0% |
| `app/services/appointments/plugin.py` | 5 | 0 | 100.0% |
| `app/services/appointments/router.py` | 98 | 0 | 100.0% |
| `app/services/appointments/schemas.py` | 40 | 0 | 100.0% |
| `app/services/appointments/service.py` | 121 | 5 | 95.9% |
| `app/services/audit/models.py` | 24 | 0 | 100.0% |
| `app/services/audit/plugin.py` | 1 | 0 | 100.0% |
| `app/services/audit/router.py` | 34 | 1 | 97.1% |
| `app/services/auth/models.py` | 18 | 0 | 100.0% |
| `app/services/auth/plugin.py` | 8 | 0 | 100.0% |
| `app/services/auth/router.py` | 60 | 4 | 93.3% |
| `app/services/auth/schemas.py` | 59 | 0 | 100.0% |
| `app/services/auth/service.py` | 47 | 0 | 100.0% |
| `app/services/doctors/models.py` | 39 | 0 | 100.0% |
| `app/services/doctors/plugin.py` | 5 | 0 | 100.0% |
| `app/services/doctors/router.py` | 76 | 0 | 100.0% |
| `app/services/doctors/schemas.py` | 48 | 0 | 100.0% |
| `app/services/doctors/service.py` | 80 | 0 | 100.0% |
| `app/services/jobs/plugin.py` | 18 | 1 | 94.4% |
| `app/services/notifications/mailer.py` | 35 | 2 | 94.3% |
| `app/services/notifications/models.py` | 28 | 0 | 100.0% |
| `app/services/notifications/plugin.py` | 6 | 0 | 100.0% |
| `app/services/notifications/reports.py` | 40 | 0 | 100.0% |
| `app/services/notifications/router.py` | 50 | 0 | 100.0% |
| `app/services/notifications/service.py` | 51 | 0 | 100.0% |
| `app/services/patients/models.py` | 22 | 0 | 100.0% |
| `app/services/patients/plugin.py` | 1 | 0 | 100.0% |
| `app/services/patients/router.py` | 60 | 3 | 95.0% |
| `app/services/patients/schemas.py` | 51 | 0 | 100.0% |
| `app/services/patients/service.py` | 35 | 0 | 100.0% |
| `app/services/records/access.py` | 30 | 2 | 93.3% |
| `app/services/records/chart.py` | 43 | 0 | 100.0% |
| `app/services/records/consultations.py` | 66 | 1 | 98.5% |
| `app/services/records/models.py` | 45 | 0 | 100.0% |
| `app/services/records/pdf.py` | 20 | 0 | 100.0% |
| `app/services/records/plugin.py` | 6 | 0 | 100.0% |
| `app/services/records/prescriptions.py` | 56 | 1 | 98.2% |
| `app/services/records/schemas.py` | 26 | 0 | 100.0% |
| `app/services/records/schemas_clinical.py` | 58 | 0 | 100.0% |
| `app/services/security/middleware.py` | 35 | 2 | 94.3% |
| `app/services/security/plugin.py` | 4 | 0 | 100.0% |
| `src/scheduling.py` | 19 | 0 | 100.0% |
