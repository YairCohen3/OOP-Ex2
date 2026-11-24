# Testing Strategy

## How we test
| Level | What | How |
|---|---|---|
| Unit | Small logic functions: QR codes, attendance cross-check, poll options | `pytest` |
| API | Every endpoint with a real (temporary) database: permissions, errors, data saved | `pytest` + FastAPI `TestClient` |
| AI | What happens when Gemini is missing or fails (no fake results) | `pytest` without an API key |
| Manual | The full flow on the live site with real phones, photos, videos and homework files | Checklist below |

All automated tests are in `test_main.py`. `conftest.py` gives every test run an empty temporary database and removes the Gemini key, so tests don't touch real data and don't call the AI.

Run: `pytest -v`

## Tests per class
| Class | What we check | Test class |
|---|---|---|
| `User` | Only listed emails get a code; code expires after 120 s and works once | `TestAuthentication` |
| `Course`, `StudentCourse` | Course ID is created; join with a wrong ID fails; only the lecturer manages students | `TestCourses` |
| `Session` | One live lecture per course; students can't start one; a new lecture always starts with check-in open; deleting a past lecture | `TestLectures`, `TestDeleteLecture` |
| `AttendanceRecord` | Check-in with the current code only; no duplicates; outsiders blocked; no check-in after "End attendance" | `TestAttendanceCheckIn`, `TestQRCode` |
| `SessionPhotoState`, `AttendanceApproval` | All cross-check cases; warning needs approval; manual count; restart; Excel has no ID column | `TestAttendanceCrossCheck`, `TestAttendanceCrossCheckFlow` |
| `ForumPost`, `ForumThreadReply` | Post, reply, empty post rejected, works after the lecture | `TestForum` |
| `Poll`, `PollVote`, `PollComment`, `PollTimeWindow` | Voting, changing a vote, closing with the lecture, time limit, comments | `TestPolls`, `TestPollChoices` |
| `Session.ai_summary` | No API key → clear error; only the lecturer can create or edit a summary | `TestLectureSummary` |
| `Assignment`, `Submission` | Upload, wrong file type, resubmit, only the lecturer approves, grade 0–100, **student can't see the grade before approval** | `TestAssignments` |
| Feedback forum, comparison | No names or grades in the forum; comparison only for the lecturer | `TestAssignments` |

## Bugs we found and fixed (with a test)
| Bug | Test |
|---|---|
| A new lecture opened with check-in already closed (an old lecture's state stayed in the database) | `test_new_lecture_starts_open_even_if_old_id_is_reused` |
| The student saw the AI grade before the lecturer approved it | `test_student_sees_grade_only_after_lecturer_approves` |
| A student could edit the lecture summary | `test_student_cannot_edit_summary` |

## Demo checklist (live site, 2–3 phones)
1. ☐ Lecturer and student log in
2. ☐ Create a course, students join with the Course ID
3. ☐ Start a lecture → QR full screen, changes every 10 s
4. ☐ Phones scan → the count goes up on the lecturer's screen
5. ☐ End attendance → a new scan is rejected
6. ☐ Class photo → Gemini count → approve → open the Excel (no ID column)
7. ☐ Manual count lower than check-ins → warning with 3 options
8. ☐ Question in the forum from a phone → the lecturer replies
9. ☐ Live poll → votes from phones → the chart updates
10. ☐ Upload a short video → summary appears for students
11. ☐ Submit homework → student sees "waiting" → lecturer approves → student sees the grade
12. ☐ End lecture → back on the course page

## Known limits
- Enrollment doesn't check that the email belongs to a registered student.
- Requests identify the user by email (no login token). Fine for a demo, not for real use.
