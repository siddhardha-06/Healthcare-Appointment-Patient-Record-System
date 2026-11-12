# Security Validation Results (Test Plan §5.1)

**Project:** Healthcare Appointment & Patient Record System · **Team:** 13 · **Run:** Sprint 3 (9–13 Nov 2026); the same checks run in CI on every pull request

| # | Check (Test Plan §5.1) | How it was tested | Result | Requirement / TC |
|---|---|---|---|---|
| 1 | Password hashing | `test_tc_sec_01_password_stored_as_bcrypt_cost_12`: stored hash starts with `$2b$12$`, 60 chars; password absent from responses and logs | Pass | HAP-SR-001 / TC-SEC-01 |
| 2 | Account lockout | `test_tc_sec_01_lockout_after_five_failures_for_15_minutes`: 6th attempt → 423, login works after 15 min, counter resets | Pass | HAP-SR-005 / TC-SEC-01 |
| 3 | Token expiry and forgery | `test_tc_sec_02_expired_and_forged_tokens_rejected`: expired → 401 TOKEN_EXPIRED; changed payload, wrong key and `alg: none` → 401 | Pass | HAP-SR-002 / TC-SEC-02 |
| 4 | RBAC | `test_tc_auth_02_patient_blocked_from_admin_endpoints` and role checks in every test file (403 for wrong roles) | Pass | HAP-SR-004 / TC-AUTH-02 |
| 5 | Record-level access | `test_tc_sec_02_patient_a_cannot_read_patient_b`, `test_record_level_access_to_appointments`, `test_tc_mr_03_other_doctor_denied_and_logged` | Pass | HAP-SR-004 / TC-SEC-02, TC-MR-03 |
| 6 | Audit logging | `test_tc_mr_03_*`: one READ entry per chart view, DENIED entry for refused access, UPDATE/DELETE refused | Pass | HAP-SR-007 / TC-MR-03 |
| 7 | Transport security | `test_https_redirect_when_forced`: with `FORCE_HTTPS=1` HTTP → 301 to HTTPS; HSTS header on HTTPS. TLS versions are set on the deployment proxy (testssl.sh run pending deployment) | Pass (app side) | HAP-SR-003 |
| 8 | Encryption at rest | `test_sensitive_fields_are_ciphertext_in_database`: diagnosis, notes and medicine columns start with `v1:` and contain no plaintext; `test_tampering_is_detected` | Pass | HAP-SR-006 |
| 9 | Input validation / injection | `test_sql_injection_in_search_is_harmless`; all inputs validated by Pydantic (422 with field name) | Pass | OWASP A03 |
| 10 | No sensitive data in errors | `test_errors_do_not_leak_internals`; emails never include clinical text (`test_tc_not_01_*`) | Pass | HAP-SR-004 |
| 11 | Privilege escalation via body | `test_role_in_request_body_is_ignored`, `test_tc_auth_01_staff_cannot_self_register` | Pass | HAP-F-001, HAP-SR-004 |
| 12 | Rate limiting | `test_login_rate_limit_returns_429`: 11th login in a minute → 429 RATE_LIMITED | Pass | SAD 3.9 |

**Not yet run:** OWASP ZAP active scan and testssl.sh need a deployed HTTPS server (see deviation 10 in `docs/sprints/deviations.md`).
