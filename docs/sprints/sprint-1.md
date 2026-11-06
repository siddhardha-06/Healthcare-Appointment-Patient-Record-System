# Sprint 1 Report (26–30 Oct 2026)

**Goal:** a working core booking flow – accounts and roles, patients, doctors and their slots, conflict-free booking, and doctors opening the charts of their own patients.

## Delivered stories

| Story | Requirement(s) | Owner | Result |
|---|---|---|---|
| S-01 Register / login with JWT | HAP-F-001, HAP-SR-001, HAP-SR-002 | Manas | Done – TC-AUTH-01 automated |
| S-02 Server-side role checks | HAP-F-002, HAP-SR-004 | Manas | Done – TC-AUTH-02 automated |
| S-03 Staff accounts | HAP-F-003 | Manas | Done |
| S-04 Lockout | HAP-SR-005 | Manas | Done |
| S-05 App skeleton + CI coverage gate | HAP-NF-005 | Manas | Done – CI fails below 70 % |
| S-06 Frontend shell | HAP-NF-004 | Manas | Done |
| S-07 – S-09 Patients, duplicate warning, search | HAP-F-010 … HAP-F-013 | Raghav | Done – TC-PAT-01 automated |
| S-10 – S-12 Doctors, availability, leave | HAP-F-020 … HAP-F-022 | Raghav | Done – TC-DOC-01 automated |
| S-13 – S-18 Search, book, conflicts, reschedule, status | HAP-F-030 … HAP-F-035 | Prithviraj | Done – TC-APT-01 … 03 automated |
| S-19 – S-21 Chart, encryption, audit log | HAP-F-040, HAP-SR-006, HAP-SR-007 | Parth | Done – TC-MR-03 automated |

**Velocity:** 66 of 66 planned story points.

## How it was built

- One branch per member (`sprint1/<name>`), one commit per file, PR reviewed by the review partner, merged with *Rebase and merge* after the `test` and `docs-check` checks passed.
- Merge order: Manas (core) → Raghav (patients, doctors) → Prithviraj (appointments) → Parth (records), because each service builds on the previous one.
- Services register themselves through `app/services/<name>/plugin.py`, so nobody had to edit a shared file.

## Demo (1-minute video)

Script: `docs/sprints/video-scripts.md` (Sprint 1 part). Video: `docs/videos/sprint-1.mp4`.

## Carried over

None. Notifications (HAP-F-050) were already published as events and are consumed in Sprint 2.
