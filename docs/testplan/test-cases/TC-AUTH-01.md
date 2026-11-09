### TC-AUTH-01 – Login with valid and invalid credentials

| Field | Content |
|---|---|
| TC ID | TC-AUTH-01 |
| Title | Login with valid and invalid credentials |
| Requirement(s) | HAP-F-001 |
| Type | Functional |
| Preconditions | Test environment running; Patient account `asha.rao@test.local` exists and is active, not locked. |
| Test data | Valid: `asha.rao@test.local` / `Test@1234`. Invalid: same email / `Wrong@999`. Staff self-registration body with `"role": "DOCTOR"`. |
| Steps | 1. Send `POST /api/v1/auth/login` with the valid email and password.<br>2. Decode the returned JWT and read the `role` and `exp` claims.<br>3. Send the same request with the wrong password.<br>4. Send `POST /api/v1/auth/register` with `"role": "DOCTOR"` in the body. |
| Expected result | • Step 1: HTTP 200 with an `accessToken`.<br>• Step 2: `role` = PATIENT; `exp` − `iat` = 1800 s.<br>• Step 3: HTTP 401 `UNAUTHENTICATED`; the message does not say whether the email or the password was wrong.<br>• Step 4: the account is created as PATIENT or the request is rejected with 403; no Doctor account is created. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_auth.py::test_tc_auth_01_valid_login_returns_jwt_with_role`<br>`tests/test_auth.py::test_tc_auth_01_wrong_password_gives_generic_401`<br>`tests/test_auth.py::test_tc_auth_01_staff_cannot_self_register` |
| Changes after the sprints | Step 4 implemented as a rejection: self-registration with a staff role returns 403 and creates nothing. |
