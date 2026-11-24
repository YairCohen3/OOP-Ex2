# Testing Strategy: SmartClass

## 1. Goals
- Prove that every requirement in `SRS.md` works — first of all the **main feature (attendance)**.
- Test each **class** of the low-level design (`Class Diagram.md`) through the logic and API that use it.
- Make the class demo safe: a short manual checklist on real phones before presenting.
- Never trust AI output blindly: test that the system **does not invent** counts, grades or summaries when the AI is unavailable.

## 2. Test Levels

| Level | What | Tool | Where |
|---|---|---|---|
| **Unit** | Pure logic functions: dynamic QR (`qr_at`, `get_qr_status`), attendance cross-check (`attendance_crosscheck`), poll option parsing (`poll_choices`). | `pytest` | `test_main.py` – classes `TestQRCode`, `TestAttendanceCrossCheck`, `TestPollChoices` |
| **API / Integration** | Every endpoint together with the database: permissions, validation, state changes, Excel output. | `pytest` + FastAPI `TestClient` + temporary SQLite DB | `test_main.py` – one test class per feature |
| **AI contract** | Behaviour when Gemini is not configured or fails (clear status, no fake data). Real Gemini quality is checked manually. | `pytest` (no key) + manual | `TestLectureSummary`, `TestAssignments`, manual checklist |
| **System / Manual** | End-to-end on real devices: phones scan the QR, real classroom photo, real video, real assignment files. | Browser, phones, Railway | Section 6 checklist |
| **Usability (KISS)** | A student reaches check-in in ≤ 3 taps; lecturer screens readable on a projector. | Manual, 2–3 classmates | Section 6 |

## 3. Test Environment
- `conftest.py` creates an **empty temporary data folder** before the app is imported (`SMARTCLASS_DATA_DIR`), so tests never touch the real `smartclass.db`, uploads or reports.
- A fixed `SMARTCLASS_QR_SECRET` makes QR codes reproducible.
- `GEMINI_API_KEY` is removed during tests, so no network calls and no costs.
- Test users are the authorized users in `main.AUTH_USERS` (one lecturer, one student) plus extra student emails for privacy tests.

**Run:**
```bash
python -m pip install -r requirements.txt
python -m pytest -v
```

## 4. Test Coverage by Class

Each class of the design and the tests that cover it:

| Class (model) | Behaviour tested | Test class in `test_main.py` |
|---|---|---|
| `User` / `AUTH_USERS` | Only authorized emails get an OTP; role comes from the list; OTP expires after 120 s; OTP single-use; wrong code rejected. | `TestAuthentication` |
| `Course` | Unique `CRS-` ID; empty name rejected; only lecturers create courses. | `TestCourses` |
| `StudentCourse` | Join by Course ID; unknown course rejected; lecturer adds/removes students; only the course lecturer manages the list. | `TestCourses` |
| `Session` (lecture) | Start returns a QR; only one active lecture per course; students cannot start; closing needs a photo count or explicit approval; closed lecture becomes past. | `TestLectures` |
| `AttendanceRecord` | Check-in with current QR; no duplicates; old QR rejected; outsiders rejected; SESSION END locks check-ins; no check-in after the lecture closed. | `TestAttendanceCheckIn`, `TestQRCode` |
| `SessionPhotoState`, `AttendanceApproval` | Cross-check rules (no photo / more check-ins / more people / match); discrepancy needs explicit approval; manual count; restart clears the round; invalid photo token rejected. | `TestAttendanceCrossCheck`, `TestAttendanceCrossCheckFlow` |
| Excel report | Columns exactly `Student Name, Institutional Email, Timestamp, Status` (**no ID numbers**); content correct; only the lecturer can download. | `TestAttendanceCrossCheckFlow` |
| `ForumPost`, `ForumThreadReply` | Post question; empty rejected; outsiders rejected; lecturer and students reply; forum open after the lecture. | `TestForum` |
| `Poll`, `PollVote`, `PollComment`, `PollTimeWindow` | Vote and live results; change vote; multiple-answer toggle; invalid options; voting locks when the lecture closes; post-lecture poll needs a time limit and closes when time is up; discussion thread. | `TestPolls`, `TestPollChoices` |
| `Session.ai_summary` (video summary) | Without an AI key the request is refused (503) and nothing is invented; only the lecturer can request; students read the saved summary. | `TestLectureSummary` |
| `Assignment`, `AssignmentBrief` | Create; invalid due date; students cannot create. | `TestAssignments` |
| `Submission`, `SubmissionDocument` | Upload; unsupported type rejected; lecturer/outsider cannot submit; resubmission replaces; no fake AI grade without a key; lecturer approves the final grade; invalid grades rejected; students cannot approve. | `TestAssignments` |
| Feedback forum | Only reviewed submissions appear; entries contain label + review only (**no grade, no name**). | `TestAssignments` |
| `AssignmentComparisonReport` | Comparison visible **only to the lecturer**; overlap pairs; AI comparison needs ≥ 2 submissions. | `TestAssignments` |

## 5. Requirement Coverage (summary)

| SRS section | Automated | Manual |
|---|---|---|
| FR-1 Authentication | ✅ | Email delivery (production only) |
| FR-2 Courses | ✅ | – |
| FR-3 Lectures | ✅ | Notification shown in UI |
| FR-4 Attendance (main) | ✅ logic, permissions, Excel | Real QR scanning on phones, real photo count with Gemini |
| FR-5 Forum | ✅ | Live refresh every 5 s |
| FR-6 Polls | ✅ | Live chart drawing |
| FR-7 Video summary | ✅ no-key behaviour, permissions | Real video → Gemini summary |
| FR-8 Assignments | ✅ permissions, privacy, grades | Real Gemini review quality, comparison report |
| NFR-1 / NFR-10 Usability, browsers | – | ✅ |
| NFR-6 Privacy | ✅ Excel columns, grade/forum/comparison visibility | – |

## 6. Manual Demo Checklist (run before presenting)

On the deployed Railway URL (HTTPS), with 2–3 real phones:

1. ☐ Lecturer logs in with OTP; student logs in on a phone.
2. ☐ Lecturer creates a course; students join with the Course ID.
3. ☐ Lecturer starts a lecture; QR on the projector changes every 10 s.
4. ☐ Each phone scans the QR → "Check-in successful"; the lecturer's count updates within 5 s.
5. ☐ A photo of the QR sent to someone outside the room fails after 10 s.
6. ☐ SESSION END → a phone scan now fails with "paused".
7. ☐ Classroom photo (use one from the course folder) → Gemini count appears.
8. ☐ Force a discrepancy (manual count lower than check-ins) → warning with options (a)/(b)/(c); try "retake" and "restart".
9. ☐ Approve → download Excel → open it: name, email, time, status, no ID column.
10. ☐ Student asks a forum question; lecturer replies; reply appears on the phone.
11. ☐ Live poll → votes from phones → chart updates; close the lecture → voting locked.
12. ☐ Past lecture: post-lecture poll with 2-minute limit; vote; wait → closed.
13. ☐ Upload a short lecture video → summary appears; student reads it.
14. ☐ Publish an assignment; submit 2 files from the assignment list → AI grade + review; lecturer approves; feedback forum shows reviews without grades; lecturer runs the comparison.
15. ☐ Repeat steps 3–4 on iPhone Safari and Android Chrome.

## 7. Entry / Exit Criteria
- **Entry:** code builds; `requirements.txt` installs; `GEMINI_API_KEY` set on the demo server.
- **Exit (ready for demo):** all automated tests pass; manual checklist steps 1–11 pass (main features); no open "Must" defect on FR-4.

## 8. Defect Handling
Bugs found in testing are logged as GitHub issues with: steps to reproduce, expected vs. actual, related FR, severity (Blocker for the demo / Major / Minor). A fix is accepted only with a test that reproduces the bug.

## 9. Known Issues Found While Writing the Tests
These were found by reviewing the API for the test plan. They do not affect the demo flow and are left for a later version:

| # | Issue | Related | Severity |
|---|---|---|---|
| 1 | `POST /api/forum/reply` (old single-reply endpoint) does not check who is replying. The UI uses the newer `/api/forum/{id}/replies`, which does. | FR-1.6 | Minor |
| 2 | `POST /api/sessions/{id}/ai-summary` (manual summary text) does not check that the caller is the lecturer. | FR-1.6 | Minor |
| 3 | `POST /api/students/enroll` does not check that the email belongs to a registered student. | FR-2.3 | Minor |
| 4 | Authentication is email-based in each request (no session token) – acceptable for the demo, not for production. | NFR-4 | Known limitation |
