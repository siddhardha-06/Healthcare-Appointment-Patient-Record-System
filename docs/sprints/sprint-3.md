# Sprint 3 Report – Testing week (9–13 Nov 2026)

**Goal:** run the whole Test Plan, update the test cases, publish the reports, and fix what testing finds.

## Work

| Story | Owner | Result |
|---|---|---|
| S-36 Update the 14 test-case documents | All (own test cases) | Done |
| S-37 Unit test + code coverage reports | Manas, Prithviraj | `docs/reports/unit-test-report.md`, `docs/reports/code-coverage-report.md` |
| S-38 Branch coverage + security validation | Raghav | `docs/reports/branch-coverage-report.md`, `docs/reports/security-validation.md` |
| S-39 System validation report | Parth | `docs/reports/system-validation-report.md` |
| TC-PERF-01 run | Prithviraj | `docs/reports/perf-summary.md` |

## Defects found by testing and fixed

| # | Found by | Defect | Fix | Owner |
|---|---|---|---|---|
| D-1 | TC-PERF-01 | Under 200 users requests waited up to 30 s: the database connection pool (5 + 10) was smaller than FastAPI's 40 worker threads | Pool sized to 20 + 20 and pre-ping enabled (`app/core/database.py`) | Manas |
| D-2 | TC-PERF-01 | Chart view loaded every doctor (500) to look up names; p95 4.4 s | Only the doctors referenced by the patient's records are loaded (`app/services/records/chart.py`) | Parth |
| D-3 | TC-PERF-01 | With 4 server workers on a new database every worker tried to create the first Admin at start-up; all but one failed and the server stopped | The losing workers roll back and continue (`app/services/auth/service.py`) | Manas |

After the fixes TC-PERF-01 passed (see the performance summary). The CI pipeline now also generates the four reports on every run (artifact `test-results`).
