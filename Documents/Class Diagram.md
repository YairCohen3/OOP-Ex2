# System Architecture & UML Diagrams

## 1. Main Software Components
The SmartClass application is composed of several decoupled modules to ensure maintainability and adherence to the KISS principle:

```mermaid
flowchart TB
    subgraph Client["Client – index.html (HTML5 + CSS + vanilla JS)"]
        SA["Student App<br/>mobile-first: QR scan, check-in, forum, polls, summaries, submissions"]
        LD["Lecturer Dashboard<br/>desktop/projector: QR projection, photo, cross-check, polls, summaries, grading"]
        MP["Mobile photo page<br/>/mobile-photo – phone camera upload"]
    end

    subgraph Server["FastAPI server – main.py"]
        AUTH["Auth Service<br/>authorized list, OTP"]
        CSM["Course & Lecture Manager<br/>courses, enrollment, lecture state"]
        ATT["Attendance Engine<br/>dynamic HMAC QR, check-in, cross-check"]
        COL["Collaboration Engine<br/>forum, polls, comments, notifications"]
        AIS["AI Service<br/>photo count, video summary, review, comparison"]
        RPT["Report Generator<br/>openpyxl Excel"]
        FILES["File Handling<br/>uploads, text extraction PDF/DOCX/ZIP"]
    end

    DB[("Database layer<br/>models.py + database.py<br/>SQLAlchemy · SQLite")]
    GEM["Google Gemini API<br/>vision · video · text"]
    STORE[("Data folder<br/>uploads · attendance_reports")]

    SA & LD & MP -->|HTTPS JSON / multipart, polling every 5 s| Server
    AUTH & CSM & ATT & COL & FILES --> DB
    ATT --> AIS
    ATT --> RPT
    AIS --> GEM
    RPT --> STORE
    FILES --> STORE
```

1. **Client Application (`index.html`, HTML5 + CSS + JavaScript):**
   * *Student App:* Mobile-first interface for QR scanning (`html5-qrcode`), poll voting, forum participation, reading summaries and assignment submission.
   * *Lecturer Dashboard:* Desktop/projector interface for lecture management, dynamic QR projection, classroom photo, cross-check result, live poll charts, summaries and grading/comparison.
   * *Mobile photo page:* A small page opened by scanning a one-time QR, so the lecturer can take the classroom photo with a phone.
2. **API Gateway & Core Logic (Python FastAPI, `main.py`):**
   * *Auth Service:* Checks the institutional authorized list and issues/validates the OTP (120 s).
   * *Course & Lecture Manager:* Course creation (unique Course ID), enrollment, one active lecture per course.
   * *Collaboration Engine:* Lecture Q&A forum with threaded replies, KISS polls (live or time-limited) with comments, in-app notifications.
3. **Attendance Engine:**
   * Generates dynamic QR codes (HMAC of lecture ID + 10-second time slot).
   * Validates check-ins, locks them on SESSION END.
   * Sends the classroom photo to the **Gemini vision model** for a head count (the lecturer can correct it), runs the cross-check and the approval flow.
   * Generates the privacy-safe `.xlsx` report via `openpyxl`.
4. **AI & LLM Service (Google Gemini API):**
   * People counting in the classroom photo.
   * Lecture video summaries via the Gemini Files API (background job, up to 500 MB).
   * Assignment deep reviews with recommended grade, and lecturer-only comparative analysis.
   * Retries on 429/5xx and falls back to a secondary model; never fabricates results.
5. **Database Layer (SQLite via SQLAlchemy, PostgreSQL-ready):** Stores users, courses, lectures, attendance, polls, forum, assignments and submissions. Files (uploads, reports) live in the data folder (`SMARTCLASS_DATA_DIR`).

---

## 2. Low-Level Class Diagram

### 2.1 Original design (milestone 2)
*This diagram illustrates the core Object-Oriented Design (OOD) of the system as first designed.*

<img width="1691" height="3068" alt="mermaid-diagram-2026-11-16-194058" src="https://github.com/user-attachments/assets/c85051a2-d4bf-4599-b86a-8a5ed758e681" />

### 2.2 Implemented data model (final)
The implemented classes as they exist in `models.py` (core) and `main.py` (extensions added during development). Extensions were added as separate classes linked by foreign key, so the original tables stayed unchanged (Open/Closed principle).

```mermaid
classDiagram
    direction LR

    class User {
        +int id
        +str email
        +str name
        +str role
    }
    class Course {
        +int id
        +str course_id
        +str title
        +str description
        +str lecturer_email
    }
    class StudentCourse {
        +int id
        +str student_email
        +str course_id
    }
    class Session {
        +int id
        +str course_id
        +bool is_active
        +str current_qr_code
        +str ai_summary
    }
    class AttendanceRecord {
        +int id
        +int session_id
        +str student_email
        +str student_name
        +datetime timestamp
    }
    class SessionQRControl {
        +int session_id
        +bool enabled
    }
    class SessionPhotoState {
        +int session_id
        +str upload_token
        +int detected_people
        +str detection_method
        +datetime updated_at
    }
    class AttendanceApproval {
        +int session_id
        +int scanned
        +int people
        +bool approved_with_discrepancy
        +datetime approved_at
    }
    class ForumPost {
        +int id
        +int session_id
        +str student_email
        +str student_name
        +str message
    }
    class ForumThreadReply {
        +int post_id
        +str author_email
        +str author_name
        +str message
    }
    class Poll {
        +int id
        +int session_id
        +str question
        +str options
        +bool is_active
    }
    class PollSettings {
        +int poll_id
        +bool allow_multiple
    }
    class PollTimeWindow {
        +int poll_id
        +datetime closes_at
    }
    class PollVote {
        +int poll_id
        +str student_email
        +str selected_option
    }
    class PollComment {
        +int poll_id
        +str email
        +str author_name
        +str message
    }
    class Assignment {
        +int id
        +str course_id
        +str title
        +str description
        +str due_date
    }
    class AssignmentBrief {
        +int assignment_id
        +str rubric
        +str extracted_instructions
        +str reference_path
    }
    class Submission {
        +int id
        +int assignment_id
        +str student_email
        +str llm_grade
        +str llm_review
        +bool final_grade_approved
    }
    class SubmissionDocument {
        +int submission_id
        +str filename
        +str stored_path
        +str extracted_text
        +str ai_status
    }
    class AssignmentComparisonReport {
        +int assignment_id
        +str report
        +datetime generated_at
    }
    class SmartNotification {
        +str recipient_email
        +str course_id
        +str kind
        +str title
        +datetime read_at
    }

    User "1" -- "0..*" Course : teaches
    User "1" -- "0..*" StudentCourse : enrolls
    Course "1" *-- "0..*" StudentCourse
    Course "1" *-- "0..*" Session : lectures
    Course "1" *-- "0..*" Assignment
    Course "1" -- "0..*" SmartNotification
    Session "1" *-- "0..*" AttendanceRecord
    Session "1" -- "0..1" SessionQRControl
    Session "1" -- "0..1" SessionPhotoState
    Session "1" -- "0..1" AttendanceApproval
    Session "1" *-- "0..*" ForumPost
    Session "1" *-- "0..*" Poll
    ForumPost "1" -- "0..*" ForumThreadReply
    Poll "1" *-- "0..*" PollVote
    Poll "1" -- "0..*" PollComment
    Poll "1" -- "0..1" PollSettings
    Poll "1" -- "0..1" PollTimeWindow
    Assignment "1" -- "0..1" AssignmentBrief
    Assignment "1" *-- "0..*" Submission
    Assignment "1" -- "0..1" AssignmentComparisonReport
    Submission "1" -- "0..1" SubmissionDocument
```

### 2.3 Service functions (main.py)
The business logic is grouped in functions that act on the classes above:

| Responsibility | Main functions |
|---|---|
| Access control | `lecturer_course`, `member_course`, `lecturer_assignment`, `assignment_for_member` |
| Dynamic QR | `qr_at`, `get_qr_status`, `qr_enabled`, `lock_attendance` |
| Attendance cross-check | `count_people_from_image`, `attendance_crosscheck`, `write_attendance_report` |
| Polls | `poll_choices`, `poll_allows_multiple` |
| AI (Gemini) | `gemini_generate`, `gemini_grade`, `gemini_compare_assignments`, `run_video_summary_job` |
| Files | `store_upload`, `extract_document_text` |
| Notifications | `notify` |

Sequence diagrams of the main flows: see `Sequence Diagrams.md`.
