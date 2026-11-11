# Unit Test Report

**Project:** Healthcare Appointment & Patient Record System · **Team:** 13 · **Generated:** 29-10-2026 17:51

Unit and API-level integration tests run with **pytest** against a fresh in-memory database per test (see Test Plan §5). Every pull request runs this suite in GitHub Actions.

| Metric | Value |
|---|---|
| Test functions | 83 |
| Passed | 83 |
| Failed | 0 |
| Skipped | 0 |
| Pass rate | 100.0% |
| Total run time | 17.0 s |

## Results per test file

| Test file | Tests | Passed | Failed | Time (s) |
|---|---|---|---|---|
| `tests/test_appointments.py` | 15 | 15 | 0 | 5.75 |
| `tests/test_auth.py` | 12 | 12 | 0 | 1.04 |
| `tests/test_crypto.py` | 3 | 3 | 0 | 0.01 |
| `tests/test_doctors.py` | 8 | 8 | 0 | 1.34 |
| `tests/test_notifications.py` | 8 | 8 | 0 | 2.12 |
| `tests/test_patients.py` | 9 | 9 | 0 | 1.48 |
| `tests/test_records_chart.py` | 5 | 5 | 0 | 1.61 |
| `tests/test_records_clinical.py` | 7 | 7 | 0 | 2.32 |
| `tests/test_scheduling.py` | 6 | 6 | 0 | 0.00 |
| `tests/test_security.py` | 10 | 10 | 0 | 1.34 |

## Failures

None.

## All tests

| Test | Result |
|---|---|
| `tests/test_appointments.py::test_tc_apt_01_search_shows_free_slots_and_booking_appears_in_schedule` | passed |
| `tests/test_appointments.py::test_slot_search_window_and_past_slots` | passed |
| `tests/test_appointments.py::test_booking_validation` | passed |
| `tests/test_appointments.py::test_tc_apt_02_twenty_bookings_of_one_slot_only_one_wins` | passed |
| `tests/test_appointments.py::test_tc_apt_02_concurrent_threads_on_shared_database` | passed |
| `tests/test_appointments.py::test_unique_index_is_the_final_guard` | passed |
| `tests/test_appointments.py::test_tc_apt_02_patient_overlap_with_another_doctor` | passed |
| `tests/test_appointments.py::test_tc_apt_03_cancel_window_and_slot_freed` | passed |
| `tests/test_appointments.py::test_tc_apt_03_status_transitions` | passed |
| `tests/test_appointments.py::test_tc_apt_03_automatic_no_show` | passed |
| `tests/test_appointments.py::test_reschedule` | passed |
| `tests/test_appointments.py::test_f035_receptionist_books_and_changes_for_patient` | passed |
| `tests/test_appointments.py::test_record_level_access_to_appointments` | passed |
| `tests/test_appointments.py::test_doctor_leave_flags_booked_appointments` | passed |
| `tests/test_appointments.py::test_no_show_job_is_registered_and_runs` | passed |
| `tests/test_auth.py::test_tc_auth_01_valid_login_returns_jwt_with_role` | passed |
| `tests/test_auth.py::test_tc_auth_01_wrong_password_gives_generic_401` | passed |
| `tests/test_auth.py::test_tc_auth_01_staff_cannot_self_register` | passed |
| `tests/test_auth.py::test_register_rejects_weak_password_and_bad_email` | passed |
| `tests/test_auth.py::test_duplicate_email_conflict` | passed |
| `tests/test_auth.py::test_tc_auth_02_patient_blocked_from_admin_endpoints` | passed |
| `tests/test_auth.py::test_missing_or_garbage_token_is_401` | passed |
| `tests/test_auth.py::test_f003_admin_creates_and_deactivates_staff` | passed |
| `tests/test_auth.py::test_admin_cannot_create_patient_or_admin_via_staff_endpoint` | passed |
| `tests/test_auth.py::test_change_password` | passed |
| `tests/test_auth.py::test_health` | passed |
| `tests/test_auth.py::test_admin_bootstrap_on_startup` | passed |
| `tests/test_crypto.py::test_round_trip_and_random_nonce` | passed |
| `tests/test_crypto.py::test_tampering_is_detected` | passed |
| `tests/test_crypto.py::test_configured_key_is_used` | passed |
| `tests/test_doctors.py::test_tc_doc_01_availability_generates_exact_slots` | passed |
| `tests/test_doctors.py::test_overlapping_availability_rejected` | passed |
| `tests/test_doctors.py::test_tc_doc_01_leave_blocks_slots_and_announces_affected_period` | passed |
| `tests/test_doctors.py::test_partial_leave_and_past_leave` | passed |
| `tests/test_doctors.py::test_f020_admin_manages_doctor_profiles` | passed |
| `tests/test_doctors.py::test_doctor_without_profile_gets_404` | passed |
| `tests/test_doctors.py::test_changing_availability_removes_free_but_keeps_booked_slots` | passed |
| `tests/test_doctors.py::test_nightly_slot_generation_job` | passed |
| `tests/test_notifications.py::test_tc_not_01_confirmation_email_and_in_app_within_a_minute` | passed |
| `tests/test_notifications.py::test_tc_not_01_reminder_sent_once_24h_before` | passed |
| `tests/test_notifications.py::test_cancel_reschedule_leave_and_prescription_notifications` | passed |
| `tests/test_notifications.py::test_failed_smtp_is_retried_then_marked_failed` | passed |
| `tests/test_notifications.py::test_f051_dashboard_figures` | passed |
| `tests/test_notifications.py::test_f052_csv_export` | passed |
| `tests/test_notifications.py::test_admin_job_runner` | passed |
| `tests/test_notifications.py::test_scheduler_loop_runs_jobs` | passed |
| `tests/test_patients.py::test_tc_pat_01_receptionist_registers_patient_and_mrn_is_generated` | passed |
| `tests/test_patients.py::test_tc_pat_01_missing_mandatory_field_is_422` | passed |
| `tests/test_patients.py::test_future_date_of_birth_rejected` | passed |
| `tests/test_patients.py::test_tc_pat_01_patient_edits_own_phone_but_not_mrn_or_dob` | passed |
| `tests/test_patients.py::test_patient_cannot_create_two_profiles` | passed |
| `tests/test_patients.py::test_mrns_are_unique` | passed |
| `tests/test_patients.py::test_f012_duplicate_warning_then_confirm` | passed |
| `tests/test_patients.py::test_f013_search_by_name_mrn_phone_and_role_check` | passed |
| `tests/test_patients.py::test_only_admin_corrects_date_of_birth` | passed |
| `tests/test_records_chart.py::test_tc_mr_03_treating_doctor_reads_chart_allergies_first` | passed |
| `tests/test_records_chart.py::test_tc_mr_03_other_doctor_denied_and_logged` | passed |
| `tests/test_records_chart.py::test_tc_mr_03_audit_rows_cannot_be_changed_or_deleted` | passed |
| `tests/test_records_chart.py::test_patient_sees_only_own_chart` | passed |
| `tests/test_records_chart.py::test_admin_reads_audit_log` | passed |
| `tests/test_records_clinical.py::test_tc_mr_01_consultation_completes_appointment_and_edit_creates_version` | passed |
| `tests/test_records_clinical.py::test_tc_mr_01_consultation_requires_check_in_and_valid_vitals` | passed |
| `tests/test_records_clinical.py::test_only_treating_doctor_writes_and_edits` | passed |
| `tests/test_records_clinical.py::test_tc_mr_02_prescription_pdf_and_patient_read_only` | passed |
| `tests/test_records_clinical.py::test_prescription_rules` | passed |
| `tests/test_records_clinical.py::test_other_patient_cannot_read_prescription` | passed |
| `tests/test_records_clinical.py::test_sensitive_fields_are_ciphertext_in_database` | passed |
| `tests/test_scheduling.py::test_monday_morning_gives_twelve_15_minute_slots` | passed |
| `tests/test_scheduling.py::test_trailing_partial_slot_is_dropped` | passed |
| `tests/test_scheduling.py::test_invalid_slot_duration_is_rejected` | passed |
| `tests/test_scheduling.py::test_end_before_start_is_rejected` | passed |
| `tests/test_scheduling.py::test_touching_intervals_do_not_overlap` | passed |
| `tests/test_scheduling.py::test_patient_with_overlapping_appointment_is_detected` | passed |
| `tests/test_security.py::test_tc_sec_01_password_stored_as_bcrypt_cost_12` | passed |
| `tests/test_security.py::test_tc_sec_01_lockout_after_five_failures_for_15_minutes` | passed |
| `tests/test_security.py::test_tc_sec_02_expired_and_forged_tokens_rejected` | passed |
| `tests/test_security.py::test_tc_sec_02_patient_a_cannot_read_patient_b` | passed |
| `tests/test_security.py::test_role_in_request_body_is_ignored` | passed |
| `tests/test_security.py::test_login_rate_limit_returns_429` | passed |
| `tests/test_security.py::test_security_headers_present` | passed |
| `tests/test_security.py::test_https_redirect_when_forced` | passed |
| `tests/test_security.py::test_sql_injection_in_search_is_harmless` | passed |
| `tests/test_security.py::test_errors_do_not_leak_internals` | passed |
