### TC-PERF-01 – Load and response-time test

| Field | Content |
|---|---|
| TC ID | TC-PERF-01 |
| Title | Load and response-time test |
| Requirement(s) | HAP-NF-001, HAP-NF-002 |
| Type | Performance |
| Preconditions | Test environment matching production size; database seeded with 500 doctors, 10,000 patients and 50,000 appointments; Locust installed. |
| Test data | Locust script: 40% slot search, 20% booking, 20% list appointments, 10% login, 10% chart view; 200 users; ramp-up 2 min; duration 10 min. |
| Steps | 1. Start the Locust run with 200 concurrent users.<br>2. Record p95 response time per endpoint and the error rate.<br>3. Run 1,000 `GET /api/v1/slots` requests for random doctors and dates and record p95. |
| Expected result | • Step 2: overall p95 ≤ 2 s; error rate < 1%.<br>• Step 3: slot search p95 ≤ 1 s.<br>• No double bookings in the database after the run. |
| Actual result | Pass – p95 157 ms overall, slot search p95 113 ms, 0 errors (200 users, 21,678 requests) |
| Status | Pass (run 29-10-2026) |
| Automated test(s) | `tests/perf/quick_load.py`, `tests/perf/locustfile.py` |
| Changes after the sprints | Run with `tests/perf/quick_load.py` (200 users, ramp-up 2/s, 60 s hold) on a 2-vCPU machine that also ran the load generator. Each user logs in once per session. Two defects found and fixed (D-1 pool size, D-2 chart query) – see docs/sprints/sprint-3.md. |
