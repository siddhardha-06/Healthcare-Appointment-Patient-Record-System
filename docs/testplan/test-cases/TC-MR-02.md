### TC-MR-02 – Prescription issued; patient views it read-only and downloads PDF

| Field | Content |
|---|---|
| TC ID | TC-MR-02 |
| Title | Prescription issued; patient views it read-only and downloads PDF |
| Requirement(s) | HAP-F-042, HAP-F-043 |
| Type | Functional |
| Preconditions | Appointment A10 COMPLETED with a consultation; its patient (Asha Rao) can log in. |
| Test data | Items: Paracetamol 650 mg / 1 tablet / 3 times a day / 5 days / after food; Cetirizine 10 mg / 1 tablet / at night / 3 days. Invalid item without `durationDays`. |
| Steps | 1. As Dr. Menon, `POST /api/v1/appointments/A10/prescriptions` with the two items.<br>2. Repeat with the invalid item.<br>3. As the patient, list own prescriptions and open the new one.<br>4. Download `GET /api/v1/prescriptions/{id}/pdf`.<br>5. As the patient, try `PUT` or `DELETE` on the prescription. |
| Expected result | • Step 1: 201 with 2 items.<br>• Step 2: 422 `VALIDATION_ERROR` naming `durationDays`.<br>• Step 3: the prescription is listed with both items.<br>• Step 4: a PDF is returned in ≤ 3 s showing clinic, doctor, MRN, date and both items.<br>• Step 5: 403; prescription unchanged. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_records_clinical.py::test_tc_mr_02_prescription_pdf_and_patient_read_only` |
| Changes after the sprints | Step 5: PUT/DELETE on a prescription return 405 (no such operation exists). The patient view hides the doctor's private notes. |
