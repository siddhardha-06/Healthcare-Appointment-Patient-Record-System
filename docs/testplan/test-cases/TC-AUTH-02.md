### TC-AUTH-02 – Patient is blocked from admin endpoints

| Field | Content |
|---|---|
| TC ID | TC-AUTH-02 |
| Title | Patient is blocked from admin endpoints |
| Requirement(s) | HAP-F-002, HAP-SR-004 |
| Type | Security |
| Preconditions | Patient and Admin test accounts exist; both can log in. |
| Test data | Patient JWT, Admin JWT. Endpoints: `GET /api/v1/admin/dashboard`, `POST /api/v1/admin/users`, `GET /api/v1/admin/reports/appointments.csv`. |
| Steps | 1. Log in as the Patient and call each admin endpoint with the Patient JWT.<br>2. Log in as the Admin and call the same endpoints.<br>3. Log in to the web UI as the Patient and check the menu. |
| Expected result | • Step 1: every call returns 403 `FORBIDDEN`; no data in the body.<br>• Step 2: every call returns 200 (or 201).<br>• Step 3: no Admin menu items are visible to the Patient. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_auth.py::test_tc_auth_02_patient_blocked_from_admin_endpoints` |
| Changes after the sprints | None. |
