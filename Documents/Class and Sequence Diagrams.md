# Class & Sequence Diagrams

## 1. Class diagram

### First version (before coding)
<img width="1691" height="3068" alt="First class diagram" src="https://github.com/user-attachments/assets/c85051a2-d4bf-4599-b86a-8a5ed758e681" />

### Final version (as implemented)
The core classes are in `models.py`. Classes we added later (photo count, approval, poll settings, lecture names…) are in `main.py`. We added them as new classes linked to the old ones instead of changing the old tables (Open/Closed principle).

```mermaid
classDiagram
    direction LR

    class User {
        email
        name
        role
    }
    class Course {
        course_id
        title
        description
        lecturer_email
    }
    class StudentCourse {
        student_email
        course_id
    }
    class Session {
        id
        course_id
        is_active
        current_qr_code
        ai_summary
    }
    class SessionTitle {
        session_id
        title
    }
    class AttendanceRecord {
        session_id
        student_email
        student_name
        timestamp
    }
    class SessionQRControl {
        session_id
        enabled
    }
    class SessionPhotoState {
        session_id
        detected_people
        detection_method
    }
    class AttendanceApproval {
        session_id
        scanned
        people
        approved_with_discrepancy
    }
    class ForumPost {
        session_id
        student_name
        message
    }
    class ForumThreadReply {
        post_id
        author_name
        message
    }
    class Poll {
        session_id
        question
        options
        is_active
    }
    class PollVote {
        poll_id
        student_email
        selected_option
    }
    class PollComment {
        poll_id
        author_name
        message
    }
    class PollTimeWindow {
        poll_id
        closes_at
    }
    class Assignment {
        course_id
        title
        description
        due_date
    }
    class AssignmentBrief {
        assignment_id
        rubric
        reference_path
    }
    class Submission {
        assignment_id
        student_email
        llm_grade
        llm_review
        final_grade_approved
    }
    class SubmissionDocument {
        submission_id
        filename
        extracted_text
        ai_status
    }
    class AssignmentComparisonReport {
        assignment_id
        report
    }
    class SmartNotification {
        recipient_email
        kind
        title
        read_at
    }

    User "1" -- "*" Course : teaches
    User "1" -- "*" StudentCourse : joins
    Course "1" *-- "*" StudentCourse
    Course "1" *-- "*" Session
    Course "1" *-- "*" Assignment
    Session "1" -- "0..1" SessionTitle
    Session "1" *-- "*" AttendanceRecord
    Session "1" -- "0..1" SessionQRControl
    Session "1" -- "0..1" SessionPhotoState
    Session "1" -- "0..1" AttendanceApproval
    Session "1" *-- "*" ForumPost
    Session "1" *-- "*" Poll
    ForumPost "1" -- "*" ForumThreadReply
    Poll "1" *-- "*" PollVote
    Poll "1" -- "*" PollComment
    Poll "1" -- "0..1" PollTimeWindow
    Assignment "1" -- "0..1" AssignmentBrief
    Assignment "1" *-- "*" Submission
    Assignment "1" -- "0..1" AssignmentComparisonReport
    Submission "1" -- "0..1" SubmissionDocument
    User "1" -- "*" SmartNotification
```

**Main functions in `main.py`:**
| Area | Functions |
|---|---|
| Permissions | `lecturer_course`, `assignment_for_member` |
| QR | `qr_at`, `get_qr_status`, `qr_enabled` |
| Attendance | `count_people_from_image`, `attendance_crosscheck`, `write_attendance_report` |
| AI | `gemini_generate`, `gemini_grade`, `run_video_summary_job` |
| Homework | `review_submission`, `review_for_response` (hides the grade from the student until it's approved) |

## 2. Sequence diagrams

### Check-in with QR

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant UI as Web page
    participant API as Server
    participant DB as Database
    actor S as Student

    L->>UI: Start new lecture
    UI->>API: POST /api/sessions/start
    API->>DB: create lecture
    API-->>UI: first QR code
    UI-->>L: QR full screen

    loop every 10 seconds
        UI->>API: GET /refresh-qr
        API-->>UI: new code
    end

    S->>UI: Scan QR with phone
    UI->>API: POST /api/attendance/scan
    API->>DB: lecture live? student in course? code current?
    alt OK
        API->>DB: save check-in
        API-->>UI: "Check-in successful"
    else problem
        API-->>UI: error (old code / closed / not in course)
    end
```

### Photo count and approval (main flow)

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant UI as Web page
    participant API as Server
    participant G as Gemini
    participant DB as Database

    L->>UI: End attendance
    UI->>API: POST /qr-control (enabled=false)
    API->>DB: lock check-in
    L->>UI: Take class photo
    UI->>API: POST /photo
    API->>G: how many people are in this photo?
    alt Gemini answered
        G-->>API: number
    else failed
        API-->>UI: please type the number
        L->>UI: types number
        UI->>API: POST /photo/manual-count
    end
    API->>DB: save count
    API-->>UI: check-ins vs people

    alt more check-ins than people
        UI-->>L: warning + 3 options
        L->>UI: restart / retake photo / approve anyway
    else OK
        UI-->>L: "Attendance is valid"
    end
    L->>UI: Approve & export
    UI->>API: POST /attendance/approve
    API->>DB: save approval
    API-->>UI: Excel ready (name, email, time, status)
```

### Lecture summary

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant UI as Web page
    participant API as Server
    participant G as Gemini
    participant DB as Database

    L->>UI: Upload recording
    UI->>API: POST /summarize-video
    API-->>UI: job started
    API->>G: upload video + "summarize this lecture"
    loop until done
        UI->>API: GET /summary-job
        API-->>UI: progress
    end
    G-->>API: summary
    API->>DB: save summary, notify students
    UI-->>L: summary shown
```

### Homework review and grade

```mermaid
sequenceDiagram
    actor S as Student
    participant UI as Web page
    participant API as Server
    participant G as Gemini
    participant DB as Database
    actor L as Lecturer

    S->>UI: Attach files, submit
    UI->>API: POST /submit-file
    API->>API: read text from PDF / Word / ZIP
    API->>G: review this against the instructions and rubric
    G-->>API: grade + review
    API->>DB: save (not approved)
    API-->>UI: "submitted"
    UI-->>S: "Waiting for your lecturer's grade"

    L->>UI: Open submissions
    UI->>API: GET /submissions
    API-->>UI: AI grade + review
    L->>UI: Approve grade (or change it)
    UI->>API: POST /grade (approved=true)
    API->>DB: save final grade, notify student

    S->>UI: Open assignment
    UI->>API: GET /my-submission
    API-->>UI: final grade + review
```
