### TC-PAT-01 – Register patient, generate MRN, edit own profile

| Field | Content |
|---|---|
| TC ID | TC-PAT-01 |
| Title | Register patient, generate MRN, edit own profile |
| Requirement(s) | HAP-F-010, HAP-F-011 |
| Type | Functional |
| Preconditions | Receptionist and Patient test accounts exist. |
| Test data | New patient: Ravi Kumar, DOB 1990-05-14, Male, mobile 9876500001. Invalid: same body without `dateOfBirth`. New phone 9876500002. |
| Steps | 1. As Receptionist, `POST /api/v1/patients` with the valid body.<br>2. Repeat with `dateOfBirth` missing.<br>3. Log in as the new patient and `PATCH /api/v1/patients/me` with the new phone.<br>4. As the patient, try to change `mrn` and `dateOfBirth`. |
| Expected result | • Step 1: 201 with an MRN matching `HAP-P-\d{6}`.<br>• Step 2: 422 `VALIDATION_ERROR` naming `dateOfBirth`; no record created.<br>• Step 3: 200; the new phone is returned by `GET /patients/me`.<br>• Step 4: 403; MRN and DOB unchanged. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_patients.py::test_tc_pat_01_receptionist_registers_patient_and_mrn_is_generated`<br>`tests/test_patients.py::test_tc_pat_01_missing_mandatory_field_is_422`<br>`tests/test_patients.py::test_tc_pat_01_patient_edits_own_phone_but_not_mrn_or_dob` |
| Changes after the sprints | Registration endpoint is `POST /api/v1/patients` (Receptionist) or `POST /api/v1/patients/me` (Patient). Added: MRNs stay unique across 25 registrations; future dates of birth are rejected. |
