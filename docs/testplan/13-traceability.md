## 13. Test Case Management & Traceability

Test cases are stored one per file in `docs/testplan/test-cases/` and tracked in GitHub Issues during execution. The full RTM is SRS §8; the mapping below shows requirement → test cases.

| Requirement(s) | Test case(s) | Automated in |
|---|---|---|
| HAP-F-001 (login, roles) | TC-AUTH-01 | `tests/test_auth.py` |
| HAP-F-002 (role-based access) | TC-AUTH-02 | `tests/test_auth.py` |
| HAP-F-010, F-011 (patient registration, profile) | TC-PAT-01 | `tests/test_patients.py` |
| HAP-F-021, F-022 (availability, leave) | TC-DOC-01 | `tests/test_doctors.py` |
| HAP-F-030, F-031 (search, book) | TC-APT-01 | `tests/test_appointments.py` |
| HAP-F-032 (conflict prevention) | TC-APT-02 | `tests/test_appointments.py` |
| HAP-F-033, F-034 (reschedule/cancel window, status lifecycle) | TC-APT-03 | `tests/test_appointments.py` |
| HAP-F-040 (care relationship) | TC-MR-03 | `tests/test_records_chart.py` |
| HAP-F-041, F-044 (consultation, versioning) | TC-MR-01 | `tests/test_records_clinical.py` |
| HAP-F-042, F-043 (prescriptions, patient view) | TC-MR-02 | `tests/test_records_clinical.py` |
| HAP-F-050 (notifications, reminder) | TC-NOT-01 | `tests/test_notifications.py` |
| HAP-NF-001, NF-002 (performance) | TC-PERF-01 | `tests/perf/quick_load.py, tests/perf/locustfile.py` |
| HAP-SR-001, SR-005 (bcrypt, lockout) | TC-SEC-01 | `tests/test_security.py` |
| HAP-SR-002, SR-004 (token expiry, record access) | TC-SEC-02 | `tests/test_security.py` |
| HAP-SR-004 (server-side role checks) | TC-AUTH-02, TC-SEC-02, TC-MR-03 | `tests/test_auth.py`, `tests/test_records_chart.py`, `tests/test_security.py` |
| HAP-SR-007 (audit log) | TC-MR-03 | `tests/test_records_chart.py` |

**Covered in sprint testing (no dedicated test case in this plan):** HAP-F-003, F-012, F-013, F-020, F-035, F-051, F-052. **Verified by other methods:** HAP-NF-003 (uptime reports, restore drill), HAP-NF-004 (usability session), HAP-NF-005 (coverage report), HAP-SR-003 (TLS scan), HAP-SR-006 (database inspection) — see §5 and §5.1.

New test cases use the owner's prefix (e.g. TC-APT-04) and are added to this table and to the RTM before execution.

**Update after the sprints (Part 3):** every test case except TC-PERF-01 is now automated with pytest and runs on every pull request in GitHub Actions; a test function named `test_tc_<id>_…` belongs to that test case. Extra tests also cover the requirements marked "sprint testing" above (HAP-F-003, F-012, F-013, F-020, F-035, F-051, F-052). Results: `docs/reports/system-validation-report.md`.

