### TC-MR-01 – Consultation saved, appointment completed, edits versioned

| Field | Content |
|---|---|
| TC ID | TC-MR-01 |
| Title | Consultation saved, appointment completed, edits versioned |
| Requirement(s) | HAP-F-041, HAP-F-044 |
| Type | Functional |
| Preconditions | Appointment A10 with Dr. Menon is CHECKED_IN; appointment A11 is BOOKED. |
| Test data | Consultation: symptoms `Fever, headache`; vitals bp 120/80, pulse 88, tempC 38.4, weightKg 61; diagnosis `Viral fever`. Edit: diagnosis `Dengue fever`, changeReason `Lab report positive`. |
| Steps | 1. As Dr. Menon, `POST /api/v1/appointments/A10/consultation` with the data.<br>2. Check A10's status.<br>3. `PUT /api/v1/consultations/{id}` with the edit.<br>4. `GET` the consultation with `?include=versions`.<br>5. Try the POST for A11.<br>6. Try `DELETE /api/v1/consultations/{id}`. |
| Expected result | • Step 1: 201, version 1.<br>• Step 2: COMPLETED.<br>• Step 3: 200, version 2.<br>• Step 4: version 2 shown by default; version 1 listed with author and timestamp and its original diagnosis.<br>• Step 5: 409 `APPOINTMENT_NOT_CHECKED_IN`.<br>• Step 6: 404 or 405 (no delete endpoint); record unchanged. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_records_clinical.py::test_tc_mr_01_consultation_completes_appointment_and_edit_creates_version`<br>`tests/test_records_clinical.py::test_tc_mr_01_consultation_requires_check_in_and_valid_vitals` |
| Changes after the sprints | Step 6: `DELETE /api/v1/consultations/{id}` returns 405 METHOD_NOT_ALLOWED. |
