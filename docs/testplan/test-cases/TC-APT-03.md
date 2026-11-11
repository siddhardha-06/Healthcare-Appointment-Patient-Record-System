### TC-APT-03 – Reschedule/cancel window and status transitions

| Field | Content |
|---|---|
| TC ID | TC-APT-03 |
| Title | Reschedule/cancel window and status transitions |
| Requirement(s) | HAP-F-033, HAP-F-034 |
| Type | Functional |
| Preconditions | Patient has appointment A1 starting in 3 h and appointment A2 starting in 1 h 50 min; Receptionist account. |
| Test data | A1, A2; free slot S2 tomorrow. |
| Steps | 1. As the Patient, cancel A1.<br>2. Search slots for A1's doctor and time.<br>3. As the Patient, cancel A2.<br>4. As the Receptionist, check in a third appointment A3 (BOOKED, today).<br>5. Try to change A3 from CHECKED_IN to BOOKED, and a COMPLETED appointment back to BOOKED.<br>6. Leave appointment A4 un-checked-in until 31 minutes after its slot end. |
| Expected result | • Step 1: 200, status CANCELLED.<br>• Step 2: A1's old slot is FREE.<br>• Step 3: 409 `CHANGE_WINDOW_CLOSED`; A2 still BOOKED.<br>• Step 4: 200, status CHECKED_IN.<br>• Step 5: 409 `INVALID_STATUS_TRANSITION` for both.<br>• Step 6: A4 status is NO_SHOW. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, 29-10-2026) |
| Automated test(s) | `tests/test_appointments.py::test_tc_apt_03_cancel_window_and_slot_freed`<br>`tests/test_appointments.py::test_tc_apt_03_status_transitions`<br>`tests/test_appointments.py::test_tc_apt_03_automatic_no_show` |
| Changes after the sprints | Step 5 also checks that a Receptionist cannot set COMPLETED and that an unknown status gives 422. |
