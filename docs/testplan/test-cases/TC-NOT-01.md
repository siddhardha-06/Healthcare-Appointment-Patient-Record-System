### TC-NOT-01 – Booking confirmation and 24-hour reminder are sent

| Field | Content |
|---|---|
| TC ID | TC-NOT-01 |
| Title | Booking confirmation and 24-hour reminder are sent |
| Requirement(s) | HAP-F-050 |
| Type | Functional |
| Preconditions | MailHog running as the SMTP server; Patient has a valid email; a doctor has FREE slots tomorrow; scheduler running. |
| Test data | Patient `asha.rao@test.local`; slot tomorrow 10:00 with Dr. K. Menon (test doctor). |
| Steps | 1. Book the 10:00 slot tomorrow as the Patient and note the time.<br>2. Open MailHog and the Patient's in-app notifications.<br>3. Set the test clock (or wait) to 24 hours before the slot start and let the reminder job run.<br>4. Check MailHog again. |
| Expected result | • Step 2: a confirmation email and an in-app notification exist within 60 s of booking, with doctor, date and time; no diagnosis or prescription text.<br>• Step 4: one reminder email is received between 23 h 55 min and 24 h 05 min before the slot start; no duplicate reminder. |
| Actual result | As expected – all steps passed. |
| Status | Pass (automated, Sprint 3 test run) |
| Automated test(s) | `tests/test_notifications.py::test_tc_not_01_confirmation_email_and_in_app_within_a_minute`<br>`tests/test_notifications.py::test_tc_not_01_reminder_sent_once_24h_before` |
| Changes after the sprints | Emails are recorded in the `email_outbox` table (MailHog optional); the test reads the outbox instead of MailHog. Reminder sent by the `reminders` job, which the test runs at controlled times. |
