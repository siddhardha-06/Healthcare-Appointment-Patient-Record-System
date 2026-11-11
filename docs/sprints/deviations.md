# Deviations from the Submitted Documents

Changes made during the sprints compared with the SRS, SAD and Test Plan (v1.0). Each one is explained in the final demo.

| # | Document / section | Planned | Built | Reason |
|---|---|---|---|---|
| 1 | SAD 3.6 Data stores | PostgreSQL | SQLite by default for development, tests and demos; PostgreSQL via `DATABASE_URL` | Zero setup for every member and for CI; the code uses only SQL both support (the partial unique index is declared for both) |
| 2 | SAD 3.6 Background jobs | APScheduler | Small built-in scheduler (`app/core/scheduler.py`) + Admin "run now" buttons | One fewer dependency; jobs can be run on demand in demos and tests |
| 3 | SAD 3.6 Frontend | React app with a build step | React 18 + htm loaded from `frontend/vendor/` (no build step, works offline) | Every member can run the UI without Node.js |
| 4 | SAD 4.3 Appointment API | `history` of status changes in GET /appointments/{id} | Not returned; status, needsReschedule and createdBy are returned | Not needed by any requirement; can be added later |
| 5 | SAD 4.4 Error codes | Code list in the context file | Added `POSSIBLE_DUPLICATE`, `PROFILE_EXISTS`, `EMAIL_TAKEN` | Needed for HAP-F-012 and HAP-F-010/F-001 duplicates |
| 6 | HAP-F-022 | Booked patients asked to reschedule | Appointments are flagged `needsReschedule`, patients notified, list shown at the front desk; nothing is cancelled automatically | Patient chooses the new time |
| 7 | TC-PERF-01 mix | 10 % of requests are logins | Each virtual user logs in once per session, then searches/books | Matches a 30-minute session; repeated bcrypt logins are not realistic traffic |
| 8 | Test Plan 6 | Separate 2-vCPU test server | Measured on a 2-vCPU machine that also ran the load generator | Only machine available; the result is therefore a lower bound |
| 9 | SAD 3.9 DoS | Nginx rate limiting | Login/register rate limit inside the app (10 per minute per IP) | Works without Nginx in development; Nginx can still be added |
| 10 | Test Plan 5.1 | OWASP ZAP and testssl.sh scans | Automated pytest checks for injection, headers, tokens and HTTPS redirect; ZAP/testssl to be run on the deployed server | No public deployment during the course |
| 11 | Test Plan 7 Schedule | Sprint 1 code merged 19–23 Oct, Sprint 2 code merged 26–30 Oct | Pull requests of both sprints merged at the end of October, strictly in sprint order (all Sprint 1 PRs before any Sprint 2 PR) | Part 1 documents took longer than planned; scope and the split of stories per member were kept |
