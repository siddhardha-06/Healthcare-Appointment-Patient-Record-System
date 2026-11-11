Pass – p95 157 ms (≤ 2000), slot search p95 113 ms (≤ 1000), errors 0.00% with 200 users

# Performance Test Summary (TC-PERF-01)

200 concurrent virtual users (ramp-up 2/s) held for 60 s against http://localhost:8766; 21678 requests.

| Endpoint | Requests | Errors | Median (ms) | p95 (ms) |
|---|---|---|---|---|
| GET /appointments | 4214 | 0 | 22 | 158 |
| GET /doctors | 2344 | 0 | 18 | 113 |
| GET /patients/me/records | 2157 | 0 | 23 | 204 |
| GET /slots | 12763 | 0 | 14 | 113 |
| POST /auth/login | 200 | 0 | 369 | 631 |
