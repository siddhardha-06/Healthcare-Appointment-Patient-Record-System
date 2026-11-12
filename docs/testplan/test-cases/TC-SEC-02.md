### TC-SEC-02 – Expired or forged tokens rejected; no access to other patients' data

| Field | Content |
|---|---|
| TC ID | TC-SEC-02 |
| Title | Expired or forged tokens rejected; no access to other patients' data |
| Requirement(s) | HAP-SR-002, HAP-SR-004 |
| Type | Security |
| Preconditions | Patients A (`HAP-P-000101`) and B (`HAP-P-000102`) exist, each with one prescription. |
| Test data | Patient A JWT; same JWT 31 minutes later; JWT with payload changed to role ADMIN and original signature; JWT signed with a wrong key. |
| Steps | 1. As A, `GET /api/v1/patients/<A id>/records`.<br>2. As A, `GET /api/v1/patients/<B id>/records` and `GET /api/v1/prescriptions/<B prescription id>`.<br>3. Repeat step 1 with the token after 31 minutes.<br>4. Repeat step 1 with the modified-payload token and with the wrong-key token. |
| Expected result | • Step 1: 200 with A's data.<br>• Step 2: 403 for both; no B data in the body.<br>• Step 3: 401 `TOKEN_EXPIRED`.<br>• Step 4: 401 `UNAUTHENTICATED` for both tokens. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_security.py::test_tc_sec_02_expired_and_forged_tokens_rejected`<br>`tests/test_security.py::test_tc_sec_02_patient_a_cannot_read_patient_b` |
| Changes after the sprints | Added an unsigned (`alg: none`) token to the forged-token checks. |
