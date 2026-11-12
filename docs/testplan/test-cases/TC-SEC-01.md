### TC-SEC-01 – Passwords are bcrypt hashes; lockout after 5 failures

| Field | Content |
|---|---|
| TC ID | TC-SEC-01 |
| Title | Passwords are bcrypt hashes; lockout after 5 failures |
| Requirement(s) | HAP-SR-001, HAP-SR-005 |
| Type | Security |
| Preconditions | Test user `lock.test@test.local` / `Test@1234`, not locked; read access to the test database. |
| Test data | Wrong password `Bad@0000` × 5, then correct password. |
| Steps | 1. Query `SELECT password_hash FROM users WHERE email = 'lock.test@test.local'`.<br>2. Search application logs for the string `Test@1234`.<br>3. Log in 5 times with the wrong password.<br>4. Log in a 6th time with the correct password.<br>5. Advance the clock by 15 minutes and log in with the correct password. |
| Expected result | • Step 1: value starts with `$2b$12$` and is 60 characters long.<br>• Step 2: no match.<br>• Steps 3–4: attempts 1–5 return 401; attempt 6 returns 423 `ACCOUNT_LOCKED`.<br>• Step 5: 200 with a token; failed-login counter reset to 0. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_security.py::test_tc_sec_01_password_stored_as_bcrypt_cost_12`<br>`tests/test_security.py::test_tc_sec_01_lockout_after_five_failures_for_15_minutes` |
| Changes after the sprints | Tests run with bcrypt cost 4 for speed; this test switches to cost 12 and checks the `$2b$12$` prefix. |
