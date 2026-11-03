# Product Backlog – Healthcare Appointment & Patient Record System

One user story per requirement in the SRS (plus engineering tasks). Story points use the Fibonacci scale (1, 2, 3, 5, 8). The same data creates the GitHub Issues, milestones and Project board (`python scripts/create_backlog.py`).

## Sprint 1 (26–30 Oct 2026, due 30-10-2026) – 66 story points

**Goal:** Core booking flow: accounts, patients, doctors and slots, conflict-free booking, chart access

| Story | Title | Requirement(s) | SP | Owner | Acceptance |
|---|---|---|---|---|---|
| S-01 | Register and log in with JWT and roles | HAP-F-001, HAP-SR-001, HAP-SR-002 | 3 | Manas | TC-AUTH-01 passes |
| S-02 | Server-side role checks on every endpoint | HAP-F-002, HAP-SR-004 | 3 | Manas | TC-AUTH-02 passes |
| S-03 | Admin creates and deactivates staff accounts | HAP-F-003 | 2 | Manas | Deactivated users cannot log in |
| S-04 | Account lockout after 5 failed logins | HAP-SR-005 | 2 | Manas | 6th attempt returns 423 |
| S-05 | App skeleton, plugin discovery, error format, CI with coverage gate | HAP-NF-005 | 3 | Manas | CI fails under 70 % coverage |
| S-06 | Web frontend shell: login, register, role menus | HAP-NF-004 | 3 | Manas | Works at 360 px |
| S-07 | Patient profile with MRN | HAP-F-010, HAP-F-011 | 3 | Raghav | TC-PAT-01 passes |
| S-08 | Duplicate patient warning | HAP-F-012 | 2 | Raghav | Same phone + DOB warns with MRN |
| S-09 | Patient search for staff | HAP-F-013 | 2 | Raghav | ≤ 1 s, 50 per page |
| S-10 | Doctor profiles | HAP-F-020 | 2 | Raghav | Only 10/15/20/30-minute slots |
| S-11 | Weekly availability generates 30 days of slots | HAP-F-021 | 5 | Raghav | TC-DOC-01 slot count exact |
| S-12 | Doctor leave blocks slots | HAP-F-022 | 3 | Raghav | TC-DOC-01 leave part passes |
| S-13 | Search doctors and free slots | HAP-F-030 | 3 | Prithviraj | TC-APT-01 passes |
| S-14 | Book an appointment | HAP-F-031 | 3 | Prithviraj | Appears in doctor's schedule |
| S-15 | Conflict prevention (row lock + partial unique index) | HAP-F-032 | 8 | Prithviraj | TC-APT-02: 1 of 20 wins |
| S-16 | Reschedule and cancel up to 2 h before | HAP-F-033 | 3 | Prithviraj | TC-APT-03 window rules |
| S-17 | Status lifecycle and check-in | HAP-F-034 | 5 | Prithviraj | Invalid transitions return 409 |
| S-18 | Receptionist books on behalf of a patient | HAP-F-035 | 2 | Prithviraj | Same conflict rules |
| S-19 | Doctor's day list and patient chart with care-relationship check | HAP-F-040 | 3 | Parth | TC-MR-03 passes |
| S-20 | AES-256-GCM encryption helper for medical fields | HAP-SR-006 | 3 | Parth | Ciphertext in DB |
| S-21 | Append-only audit log | HAP-SR-007 | 3 | Parth | UPDATE/DELETE refused |

## Sprint 2 (2–6 Nov 2026, due 06-11-2026) – 47 story points

**Goal:** Clinical records, prescriptions, notifications, reports, security hardening, performance kit

| Story | Title | Requirement(s) | SP | Owner | Acceptance |
|---|---|---|---|---|---|
| S-22 | Consultation notes complete the visit | HAP-F-041 | 5 | Parth | TC-MR-01 passes |
| S-23 | Prescriptions with PDF | HAP-F-042 | 5 | Parth | TC-MR-02 PDF part |
| S-24 | Patient views own records read-only | HAP-F-043 | 3 | Parth | TC-MR-02 read-only part |
| S-25 | Versioned, never-deleted records | HAP-F-044 | 3 | Parth | Edit creates version 2 |
| S-26 | Notifications and 24-hour reminders | HAP-F-050 | 5 | Manas | TC-NOT-01 passes |
| S-27 | Admin dashboard | HAP-F-051 | 3 | Manas | Figures match the database |
| S-28 | CSV export of appointments | HAP-F-052 | 2 | Manas | ≤ 366 days, audited |
| S-29 | Background job scheduler (reminders, no-shows, slots) | HAP-F-034, HAP-F-050, HAP-F-021 | 3 | Manas | Jobs runnable by Admin |
| S-30 | Automatic NO_SHOW job | HAP-F-034 | 2 | Prithviraj | NO_SHOW 30 min after slot end |
| S-31 | Front-desk screen: arrivals, check-in, book for patient | HAP-F-034, HAP-F-035 | 3 | Prithviraj | Usable on a tablet |
| S-32 | Load-test kit and performance run | HAP-NF-001, HAP-NF-002 | 5 | Prithviraj | TC-PERF-01 passes |
| S-33 | Security hardening: rate limit, headers, HTTPS redirect | HAP-SR-003, HAP-SR-005 | 3 | Raghav | 429 after 10 attempts/min |
| S-34 | Reception patient screen and nightly slot job | HAP-F-011, HAP-F-021 | 3 | Raghav | Walk-in registration in UI |
| S-35 | Demo data for sprint videos | HAP-NF-004 | 2 | Raghav | One command seeds everything |

## Sprint 3 (9–13 Nov 2026, due 13-11-2026) – 8 story points

**Goal:** Testing week: test-case updates, reports, fixes from testing (spill-over sprint)

| Story | Title | Requirement(s) | SP | Owner | Acceptance |
|---|---|---|---|---|---|
| S-36 | Update test cases after the sprints | HAP-NF-005 | 2 | Manas | All 14 TC documents updated |
| S-37 | Unit test and code coverage reports | HAP-NF-005 | 2 | Prithviraj | Reports in docs/reports |
| S-38 | Branch coverage report and security validation | HAP-SR-004 | 2 | Raghav | Reports in docs/reports |
| S-39 | System validation report | HAP-NF-005 | 2 | Parth | 14 test cases reported |

## Story points per member

| Member | GitHub | Sprint 1 | Sprint 2 | Sprint 3 | Total |
|---|---|---|---|---|---|
| Manas | siddhardha-06 | 16 | 13 | 2 | 31 |
| Prithviraj | Prithviraj-techie | 24 | 10 | 2 | 36 |
| Parth | Parthkale64 | 9 | 16 | 2 | 27 |
| Raghav | RAGHAV-BUDUR | 17 | 8 | 2 | 27 |

Sprint dry run: 12–16 Oct (practice). Backlog entries may still be changed on 26 Oct. All sprints run one week after the course dates (see docs/sprints/deviations.md, #11).
