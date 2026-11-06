"""TC-PERF-01 load test (HAP-NF-001, HAP-NF-002).

    pip install locust
    locust -f tests/perf/locustfile.py --host http://localhost:8000 --users 200 --spawn-rate 2 --run-time 10m --headless --csv docs/reports/perf

Pass: p95 of all requests <= 2000 ms, error rate < 1 %, p95 of 'GET /slots' <= 1000 ms.
Mix: each user logs in once per session (on_start), then 40 % slot search, 20 % booking attempts,
20 % list appointments, 10 % doctor search, 10 % chart view.
"""
import random
from datetime import date, timedelta

from locust import HttpUser, between, task

PASSWORD = "Perf@1234"


class PatientUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.n = random.randrange(10_000)
        r = self.client.post("/api/v1/auth/login", json={"email": f"perf.pat{self.n}@hap.local", "password": PASSWORD},
                             name="POST /auth/login")
        self.headers = {"Authorization": f"Bearer {r.json().get('accessToken', '')}"}
        doctors = self.client.get("/api/v1/doctors", headers=self.headers, name="GET /doctors").json()
        self.doctor_ids = [d["id"] for d in doctors] or [1]

    @task(40)
    def search_slots(self):
        day = (date.today() + timedelta(days=random.randint(0, 30))).isoformat()
        self.client.get(f"/api/v1/slots?doctorId={random.choice(self.doctor_ids)}&date={day}", headers=self.headers,
                        name="GET /slots")

    @task(20)
    def try_booking(self):
        day = (date.today() + timedelta(days=random.randint(1, 30))).isoformat()
        r = self.client.get(f"/api/v1/slots?doctorId={random.choice(self.doctor_ids)}&date={day}", headers=self.headers,
                            name="GET /slots")
        slots = r.json().get("slots", []) if r.status_code == 200 else []
        if slots:
            with self.client.post("/api/v1/appointments", headers=self.headers, name="POST /appointments",
                                  json={"slotId": random.choice(slots)["slotId"], "reason": "Load test visit"},
                                  catch_response=True) as resp:
                if resp.status_code in (201, 409, 404):   # 409/404 are correct business answers under load
                    resp.success()

    @task(20)
    def my_appointments(self):
        self.client.get("/api/v1/appointments", headers=self.headers, name="GET /appointments")

    @task(10)
    def doctor_search(self):
        self.client.get("/api/v1/doctors?specialization=Cardiology", headers=self.headers, name="GET /doctors")

    @task(10)
    def my_chart(self):
        self.client.get("/api/v1/patients/me/records", headers=self.headers, name="GET /patients/me/records")
