"""TC-PERF-01 without extra tools: N concurrent virtual users hit a running server for a fixed time.

    DATABASE_URL=sqlite:///./perf.db python tests/perf/seed_perf.py
    LOGIN_RATE_PER_MINUTE=100000 DATABASE_URL=sqlite:///./perf.db uvicorn app.main:create_app --factory --port 8000 --workers 4
    python tests/perf/quick_load.py --host http://localhost:8000 --users 200 --seconds 120 --out docs/reports

Each virtual user logs in once (a session lasts 30 minutes), then loops: 60 % slot search, 20 % own appointments,
10 % doctor search, 10 % own records. Login cost (bcrypt, cost 12) is measured on the session start.
Pass criteria (HAP-NF-001 / NF-002): p95 of all requests <= 2000 ms, errors < 1 %, p95 of GET /slots <= 1000 ms.
Writes perf-summary.md (first line = verdict, read by scripts/generate_reports.py).
"""
import argparse
import random
import statistics
import threading
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import httpx

PASSWORD = "Perf@1234"


def p95(values):
    if not values:
        return 0.0
    v = sorted(values)
    return v[min(len(v) - 1, int(round(0.95 * (len(v) - 1))))]


def user_loop(host, stop_at, samples, errors, lock, seed):
    rnd = random.Random(seed)
    with httpx.Client(base_url=host, timeout=30) as c:
        def call(name, method, url, **kw):
            t0 = time.perf_counter()
            try:
                r = c.request(method, url, **kw)
                ok = r.status_code < 500 and r.status_code not in (401, 429)
            except httpx.HTTPError:
                r, ok = None, False
            ms = (time.perf_counter() - t0) * 1000
            with lock:
                samples[name].append(ms)
                if not ok:
                    errors[name] += 1
            return r

        n = rnd.randrange(10_000)
        r = call("POST /auth/login", "POST", "/api/v1/auth/login", json={"email": f"perf.pat{n}@hap.local", "password": PASSWORD})
        token = r.json().get("accessToken", "") if r is not None and r.status_code == 200 else ""
        h = {"Authorization": f"Bearer {token}"}
        r = call("GET /doctors", "GET", "/api/v1/doctors", headers=h)
        doctors = [d["id"] for d in (r.json() if r is not None and r.status_code == 200 else [])] or [1]
        while time.time() < stop_at:
            pick = rnd.random()
            day = (date.today() + timedelta(days=rnd.randint(0, 30))).isoformat()
            if pick < 0.6:
                call("GET /slots", "GET", f"/api/v1/slots?doctorId={rnd.choice(doctors)}&date={day}", headers=h)
            elif pick < 0.8:
                call("GET /appointments", "GET", "/api/v1/appointments", headers=h)
            elif pick < 0.9:
                call("GET /doctors", "GET", "/api/v1/doctors?specialization=Cardiology", headers=h)
            else:
                call("GET /patients/me/records", "GET", "/api/v1/patients/me/records", headers=h)
            time.sleep(rnd.uniform(0.5, 1.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://localhost:8000")
    ap.add_argument("--users", type=int, default=200)
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--spawn-rate", type=float, default=2.0, help="new users per second (Locust default in Test Plan)")
    ap.add_argument("--out", default="docs/reports")
    a = ap.parse_args()
    samples, errors, lock = defaultdict(list), defaultdict(int), threading.Lock()
    stop_at = time.time() + a.users / a.spawn_rate + a.seconds  # ramp-up, then the measured period
    threads = [threading.Thread(target=user_loop, args=(a.host, stop_at, samples, errors, lock, i), daemon=True)
               for i in range(a.users)]
    for i, t in enumerate(threads):
        t.start()
        time.sleep(1.0 / a.spawn_rate)  # ramp-up
    for t in threads:
        t.join()
    all_ms = [x for v in samples.values() for x in v]
    total, errs = len(all_ms), sum(errors.values())
    overall, slots = p95(all_ms), p95(samples.get("GET /slots", []))
    ok = overall <= 2000 and slots <= 1000 and (errs / max(total, 1)) < 0.01
    verdict = (f"{'Pass' if ok else 'Fail'} – p95 {overall:.0f} ms (≤ 2000), slot search p95 {slots:.0f} ms (≤ 1000), "
               f"errors {100 * errs / max(total, 1):.2f}% with {a.users} users")
    lines = [verdict, "", f"# Performance Test Summary (TC-PERF-01)", "",
             f"{a.users} concurrent virtual users (ramp-up {a.spawn_rate:g}/s) held for {a.seconds} s against {a.host}; {total} requests.", "",
             "| Endpoint | Requests | Errors | Median (ms) | p95 (ms) |", "|---|---|---|---|---|"]
    for name, v in sorted(samples.items()):
        lines.append(f"| {name} | {len(v)} | {errors[name]} | {statistics.median(v):.0f} | {p95(v):.0f} |")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "perf-summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
