### TC-APT-01 – Search free slots and book an appointment

| Field | Content |
|---|---|
| TC ID | TC-APT-01 |
| Title | Search free slots and book an appointment |
| Requirement(s) | HAP-F-030, HAP-F-031 |
| Type | Functional |
| Preconditions | Dr. K. Menon (Cardiology) has FREE slots on the test date; Patient account exists. |
| Test data | Specialization `Cardiology`; date = today + 3 days; slot 10:15; reason `Chest pain on exertion`. |
| Steps | 1. As the Patient, search doctors with specialization Cardiology.<br>2. Request free slots for Dr. Menon on the test date.<br>3. Book the 10:15 slot with the reason.<br>4. As Dr. Menon, open the daily schedule for that date. |
| Expected result | • Step 1: only active cardiologists listed.<br>• Step 2: FREE slots only, in time order; no BOOKED, BLOCKED or past slots.<br>• Step 3: 201 with status BOOKED; the slot is no longer in the free list.<br>• Step 4: the appointment appears within 5 s with the patient's name and reason. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, 29-10-2026) |
| Automated test(s) | `tests/test_appointments.py::test_tc_apt_01_search_shows_free_slots_and_booking_appears_in_schedule` |
| Changes after the sprints | None. |
