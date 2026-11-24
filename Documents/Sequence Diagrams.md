# Sequence Diagrams: SmartClass

The diagrams below show how the main flows run through the system. Participant names match the code:

| Participant | In the code |
|---|---|
| Student UI / Lecturer UI | `index.html` (single page, polls the API every 5 s) |
| API | `main.py` (FastAPI endpoints) |
| DB | `database.py` + `models.py` (SQLAlchemy, SQLite) |
| Gemini | Google Gemini REST API (`gemini_generate`, Files API) |

Each diagram references the use case (`Use Cases.md`) it implements.

---

## 1. Login with OTP (UC-1)

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Web UI
    participant API as FastAPI (main.py)

    U->>UI: Enter institutional email (no role choice)
    UI->>API: POST /api/auth/request-otp?email
    alt email not in institution list
        API-->>UI: 403 "Email not found in institution records"
    else authorized
        API->>API: create 4-digit code, expires in 120 s (otp_store)
        API-->>UI: 200 {expires_in_seconds: 120} (demo: debug_code)
        UI-->>U: Show code field + countdown
        U->>UI: Enter code
        UI->>API: POST /api/auth/verify-otp?email&code
        alt expired or wrong
            API-->>UI: 401 error (user may resend)
        else valid
            API->>API: compare_digest, remove code
            API-->>UI: {email, name, role from the institution list}
            UI-->>U: Open "My Courses"
        end
    end
```

---

## 2. Start lecture and student QR check-in (UC-5, UC-6)

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant LUI as Lecturer UI
    participant API as FastAPI
    participant DB as DB
    participant SUI as Student UI
    actor S as Student

    L->>LUI: Create new lecture
    LUI->>API: POST /api/sessions/start?course_id&lecturer_email
    API->>DB: check ownership, no other active lecture
    API->>DB: INSERT Session(is_active=true)
    API->>DB: clear leftover attendance state for this id, notify students
    API-->>LUI: {session_id, qr_code, expires_in_seconds}
    LUI-->>L: QR full screen (locked until End attendance)

    loop every 10 s while attendance is open
        LUI->>API: GET /api/sessions/{id}/refresh-qr
        API->>API: qr = HMAC(secret, session_id : time_slot)
        API-->>LUI: new qr_code
        LUI-->>L: Project new QR + progress bar
    end

    S->>SUI: Open green lecture, press "Check in"
    SUI->>SUI: Open camera (html5-qrcode), read QR
    SUI->>API: POST /api/attendance/scan?session_id&student_email&qr_code
    API->>DB: lecture active? student enrolled?
    API->>API: qr == current slot (or previous slot within 2 s)?
    alt invalid / expired / locked / not enrolled
        API-->>SUI: 400 / 403 / 409 with message
    else already checked in
        API-->>SUI: "Attendance already recorded"
    else valid
        API->>DB: INSERT AttendanceRecord(email, name, timestamp)
        API-->>SUI: "Check-in successful!"
    end

    loop every 5 s
        LUI->>API: GET /api/sessions/{id}/live-state
        API-->>LUI: checked_in_count, students, crosscheck
    end
```

---

## 3. End attendance (SESSION END), classroom photo, cross-check and Excel (UC-7 – main flow)

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant LUI as Lecturer UI
    participant API as FastAPI
    participant DB as DB
    participant G as Gemini

    L->>LUI: Press End attendance
    LUI->>API: POST /api/sessions/{id}/qr-control?enabled=false
    API->>DB: SessionQRControl.enabled = false (check-ins locked)
    API-->>LUI: qr_enabled = false
    LUI-->>L: Leave full screen, show "Classroom photo" step

    L->>LUI: Take / upload classroom photo
    LUI->>API: POST /api/sessions/{id}/photo (image, upload token)
    API->>API: detect real image type, resize (prepare_photo)
    API->>G: "Count the people in this classroom photo" + image
    alt Gemini OK
        G-->>API: {"people": N}
        API->>DB: SessionPhotoState.detected_people = N
    else Gemini failed / no key
        API-->>LUI: 503 "enter the verified count manually"
        L->>LUI: Type verified count
        LUI->>API: POST /api/sessions/{id}/photo/manual-count?people=N
        API->>DB: detected_people = N (lecturer verified)
    end
    API->>API: attendance_crosscheck(scanned, N)
    API-->>LUI: crosscheck {status, scanned, people, message}

    alt scanned > people (discrepancy)
        LUI-->>L: Warning + options (a) restart (b) retake (c) approve
        opt (a) restart attendance
            L->>LUI: Restart
            LUI->>API: POST /api/sessions/{id}/reset-attendance
            API->>DB: delete check-ins + photo count, re-enable QR
            API-->>LUI: new QR (back to check-in)
        end
        opt (b) retake photo
            L->>LUI: Retake
            Note over LUI,G: repeat the photo step
        end
        opt (c) approve anyway
            L->>LUI: Approve
            LUI->>API: POST /api/sessions/{id}/attendance/approve?approve_mismatch=true
        end
    else people >= scanned (valid)
        LUI-->>L: "Attendance is valid"
        L->>LUI: Approve
        LUI->>API: POST /api/sessions/{id}/attendance/approve
    end

    API->>DB: AttendanceApproval(scanned, people, approved_with_discrepancy)
    API->>API: write_attendance_report() with openpyxl
    Note right of API: Columns: Student Name, Institutional Email,<br/>Timestamp, Status (no ID numbers)
    API-->>LUI: excel_report_generated
    LUI-->>L: Attendance section collapses to a summary line
    L->>LUI: Download Excel
    LUI->>API: GET /api/sessions/{id}/attendance-report
    API-->>LUI: attendance_session_{id}.xlsx
```

---

## 4. Live poll (UC-9, UC-10)

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant LUI as Lecturer UI
    participant API as FastAPI
    participant DB as DB
    participant SUI as Student UI
    actor S as Student

    L->>LUI: Question + options (+ duration if lecture is past)
    LUI->>API: POST /api/polls/create
    API->>API: validate 2–12 distinct options, past lecture needs duration
    API->>DB: INSERT Poll (+ PollTimeWindow if past lecture)
    API-->>LUI: poll_id

    S->>SUI: Choose option
    SUI->>API: POST /api/polls/vote?poll_id&student_email&selected_option
    API->>DB: poll active? window not expired? lecture still live?
    alt closed / expired
        API-->>SUI: 400 "Poll is closed"
    else open
        API->>DB: insert or replace the student's vote
        API-->>SUI: "Vote recorded"
    end

    loop every 5 s
        LUI->>API: GET /api/sessions/{id}/polls
        SUI->>API: GET /api/sessions/{id}/polls
        API-->>LUI: results per option + comments
        API-->>SUI: results per option + comments
        Note over LUI,SUI: live bar chart re-drawn
    end

    S->>SUI: Write comment
    SUI->>API: POST /api/polls/{id}/comments
    API->>DB: INSERT PollComment

    L->>LUI: Close lecture
    LUI->>API: POST /api/sessions/{id}/close
    API->>DB: Session.is_active = false, all its polls is_active = false
```

---

## 5. AI lecture summary (UC-11)

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant LUI as Lecturer UI
    participant API as FastAPI
    participant BG as Background job
    participant G as Gemini
    participant DB as DB

    L->>LUI: Upload video (≤ 500 MB) or paste link
    LUI->>API: POST /api/sessions/{id}/summarize-video (multipart)
    API->>API: check ownership, key, format, size, stream file to temp
    API->>BG: add_task(run_video_summary_job)
    API-->>LUI: {state: "running"}

    BG->>G: Files API upload (stage "sending")
    loop until file is ACTIVE (stage "processing")
        BG->>G: GET file state
    end
    BG->>G: generateContent(video + summary prompt) (stage "summarizing")
    G-->>BG: summary text
    BG->>DB: Session.ai_summary = text, notify students
    BG->>G: delete uploaded file

    loop every few seconds
        LUI->>API: GET /api/sessions/{id}/summary-job
        API-->>LUI: state, stage, elapsed
    end
    LUI-->>L: Summary ready
```

---

## 6. Assignment submission, AI review, approval and comparison (UC-14, UC-15, UC-17)

```mermaid
sequenceDiagram
    actor S as Student
    participant SUI as Student UI
    participant API as FastAPI
    participant DB as DB
    participant G as Gemini
    participant LUI as Lecturer UI
    actor L as Lecturer

    S->>SUI: Click assignment, attach up to 10 files in the popup
    SUI->>API: POST /api/assignments/{id}/submit-file
    API->>API: store_upload(): type & size check, extract text (PDF/DOCX/ZIP/code)
    API->>DB: upsert Submission + SubmissionDocument (ai_status = pending)
    API->>G: gemini_grade(instructions, rubric, answer)
    alt review OK
        G-->>API: {score, review, criteria, strengths, improvements}
        API->>DB: llm_grade, llm_review, final_grade_approved = false
    else failed
        API->>DB: ai_status = review_failed
        API->>API: background retries after 20 s, 60 s, 180 s
    end
    API-->>SUI: "submitted" (no grade, no review)
    SUI-->>S: "Waiting for your lecturer's grade"

    L->>LUI: Open submissions
    LUI->>API: GET /api/assignments/{id}/submissions
    API-->>LUI: all submissions with AI grade and review
    L->>LUI: Keep / change grade, Approve
    LUI->>API: POST /api/assignments/submission/{sid}/grade?grade&approved=true
    API->>DB: final grade saved, notify student

    SUI->>API: GET /api/assignments/{id}/my-submission
    API-->>SUI: final grade + review (only now, after approval)
    SUI->>API: GET /api/assignments/{id}/feedback-forum
    API-->>SUI: reviews of approved submissions as "Submission N" (no grades, no names)

    L->>LUI: Run AI comparison
    LUI->>API: POST /api/assignments/{id}/run-comparison
    API->>G: compare all extracted submissions
    G-->>API: comparative report
    API->>DB: AssignmentComparisonReport
    LUI->>API: GET /api/assignments/{id}/comparison
    API-->>LUI: report + label mapping + average grade + overlap pairs (lecturer only)
```
