# System Validation Report

**Project:** Healthcare Appointment & Patient Record System · **Team:** 13 · **Generated:** 12-11-2026 21:10

Each test case of the Test Plan is automated as one or more pytest tests named `test_tc_<id>_…`. They exercise the running FastAPI application end to end through its REST API (system level). A test case passes only if all of its automated tests pass.

| TC ID | Title | Requirement(s) | Automated tests | Result |
|---|---|---|---|---|
| TC-AUTH-01 | Login with valid and invalid credentials | HAP-F-001 | `test_tc_auth_01_valid_login_returns_jwt_with_role`<br>`test_tc_auth_01_wrong_password_gives_generic_401`<br>`test_tc_auth_01_staff_cannot_self_register` | Pass |
| TC-AUTH-02 | Patient is blocked from admin endpoints | HAP-F-002, HAP-SR-004 | `test_tc_auth_02_patient_blocked_from_admin_endpoints` | Pass |
| TC-NOT-01 | Booking confirmation and 24-hour reminder are sent | HAP-F-050 | `test_tc_not_01_confirmation_email_and_in_app_within_a_minute`<br>`test_tc_not_01_reminder_sent_once_24h_before` | Pass |
| TC-PAT-01 | Register patient, generate MRN, edit own profile | HAP-F-010, HAP-F-011 | `test_tc_pat_01_receptionist_registers_patient_and_mrn_is_generated`<br>`test_tc_pat_01_missing_mandatory_field_is_422`<br>`test_tc_pat_01_patient_edits_own_phone_but_not_mrn_or_dob` | Pass |
| TC-DOC-01 | Availability generates slots; leave blocks them | HAP-F-021, HAP-F-022 | `test_tc_doc_01_availability_generates_exact_slots`<br>`test_tc_doc_01_leave_blocks_slots_and_announces_affected_period` | Pass |
| TC-SEC-01 | Passwords are bcrypt hashes; lockout after 5 failures | HAP-SR-001, HAP-SR-005 | `test_tc_sec_01_password_stored_as_bcrypt_cost_12`<br>`test_tc_sec_01_lockout_after_five_failures_for_15_minutes` | Pass |
| TC-SEC-02 | Expired or forged tokens rejected; no access to other patients' data | HAP-SR-002, HAP-SR-004 | `test_tc_sec_02_expired_and_forged_tokens_rejected`<br>`test_tc_sec_02_patient_a_cannot_read_patient_b` | Pass |
| TC-APT-01 | Search free slots and book an appointment | HAP-F-030, HAP-F-031 | `test_tc_apt_01_search_shows_free_slots_and_booking_appears_in_schedule` | Pass |
| TC-APT-02 | Double booking and patient overlap are prevented | HAP-F-032 | `test_tc_apt_02_twenty_bookings_of_one_slot_only_one_wins`<br>`test_tc_apt_02_concurrent_threads_on_shared_database`<br>`test_tc_apt_02_patient_overlap_with_another_doctor` | Pass |
| TC-APT-03 | Reschedule/cancel window and status transitions | HAP-F-033, HAP-F-034 | `test_tc_apt_03_cancel_window_and_slot_freed`<br>`test_tc_apt_03_status_transitions`<br>`test_tc_apt_03_automatic_no_show` | Pass |
| TC-PERF-01 | Load and response-time test | HAP-NF-001, HAP-NF-002 | `tests/perf/locustfile.py`, `tests/perf/quick_load.py` | Pass – p95 157 ms (≤ 2000), slot search p95 113 ms (≤ 1000), errors 0.00% with 200 users |
| TC-MR-01 | Consultation saved, appointment completed, edits versioned | HAP-F-041, HAP-F-044 | `test_tc_mr_01_consultation_completes_appointment_and_edit_creates_version`<br>`test_tc_mr_01_consultation_requires_check_in_and_valid_vitals` | Pass |
| TC-MR-02 | Prescription issued; patient views it read-only and downloads PDF | HAP-F-042, HAP-F-043 | `test_tc_mr_02_prescription_pdf_and_patient_read_only` | Pass |
| TC-MR-03 | Doctor without care relationship is denied and the attempt is logged | HAP-F-040, HAP-SR-004, HAP-SR-007 | `test_tc_mr_03_treating_doctor_reads_chart_allergies_first`<br>`test_tc_mr_03_other_doctor_denied_and_logged`<br>`test_tc_mr_03_audit_rows_cannot_be_changed_or_deleted` | Pass |

**14 of 14 test cases passed.**
