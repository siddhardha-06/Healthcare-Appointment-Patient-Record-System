# Sprint Video Scripts

Start the app with demo data first:

```
pip install -r requirements.txt
python scripts/seed_demo.py --reset
uvicorn app.main:create_app --factory
```

Open http://localhost:8000. Every demo account uses the password `Demo@1234` (Admin: `admin@hap.local` / `Admin@1234`).
Record with the Windows Game Bar (Win + Alt + R) or OBS and save into `docs/videos/`.

## Sprint 1 – 1 minute (`docs/videos/sprint-1.mp4`)

| Time | Who | Show |
|---|---|---|
| 0:00 | – | Title: "Team 13 – Sprint 1: core booking flow" |
| 0:05 | Patient (register a new one) | Register → log in → My profile → Create profile → MRN appears |
| 0:20 | Patient | Appointments → Cardiology → Dr K Menon → tomorrow → pick a time → reason → Book |
| 0:35 | Second browser window, another patient | Try the same slot → "Someone just booked this time" (conflict prevention, HAP-F-032) |
| 0:45 | Doctor `dr.menon@hap.local` | My day → open the patient → chart with allergy banner |
| 0:55 | GitHub | Actions tab: green `test` and `docs-check` on the merged PRs |

## Sprint 2 – 2 minutes (`docs/videos/sprint-2.mp4`)

| Time | Who | Show |
|---|---|---|
| 0:00 | – | Title: "Team 13 – Sprint 2: complete product" |
| 0:05 | Receptionist `reception@hap.local` | Front desk → check in the patient booked for tomorrow (change the date) |
| 0:20 | Doctor | My day → open → vitals, symptoms, diagnosis, one medicine → Save consultation |
| 0:45 | Patient | My records → diagnosis + prescription → Download PDF → open it |
| 1:00 | Patient | Notifications → booking confirmation and "prescription ready" |
| 1:10 | Doctor | My availability → mark tomorrow as leave → patient gets a "please reschedule" notification |
| 1:25 | Admin | Dashboard → utilisation, no-show rate → Download CSV |
| 1:40 | Admin | Staff → create a receptionist (one-time password) → deactivate |
| 1:50 | GitHub | Actions → latest CI run → coverage 97 %, artifact `test-results` |
