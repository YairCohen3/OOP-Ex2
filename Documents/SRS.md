# Software Requirements Specification (SRS): SmartClass

| | |
|---|---|
| **Project** | SmartClass – Web-based teaching tool (Ex2, Introduction to Software Engineering) |
| **Version** | 1.0 |
| **Date** | 24/11/2026 |
| **Related documents** | `README.md`, `Statment of Work.md`, `Technical Tools Report.md`, `Class Diagram.md`, `Use Cases.md`, `Sequence Diagrams.md`, `Testing Strategy.md` |

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements of **SmartClass**, a KISS web application that lets a lecturer run a class (attendance, Q&A, polls, lecture summaries, assignment reviews) and lets students take part from their smartphone. It is the reference for design, implementation, testing and the in-class demo.

### 1.2 Scope
SmartClass is a single web application (FastAPI backend + one responsive HTML/JS page) with five features:

1. **Smart attendance** – dynamic QR check-in, classroom photo head-count with AI, cross-check, Excel report. *(main feature)*
2. **Lecture Q&A forum** – questions and replies during and after the lecture.
3. **KISS polls** – multiple-choice polls with a live results chart and a comment thread.
4. **AI lecture summary** – summary of a lecture recording (uploaded video or public link).
5. **Assignments with LLM review** – AI grade + deep review, lecturer approval, shared feedback forum without grades, lecturer-only comparison.

**Out of scope** (per the assignment guidelines): integration with Moodle, Zoom or university information systems; self sign-up; production-grade identity management.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| Course ID | Unique code generated for each course (e.g. `CRS-482`), given to students in class to join. |
| Lecture / Session | One class meeting under a course. **Active** (green) while running, **past** (grey) after it is closed. |
| SESSION END | The lecturer's action that locks QR check-ins before the classroom photo is taken. |
| Cross-check | Comparison between number of QR check-ins and number of people counted in the photo. |
| OTP | One-time verification code used to log in. |
| LLM | Large Language Model (Google Gemini). |

### 1.4 Overview
Section 2 describes the product context, users and constraints. Section 3 lists the functional requirements per feature, each with an ID (`FR-x.y`). Section 4 lists the non-functional requirements (`NFR-x`). Section 5 gives the data requirements and Section 6 the traceability to the assignment features.

---

## 2. Overall Description

### 2.1 Product perspective
SmartClass is a standalone system. External services used:

| External system | Use |
|---|---|
| Google Gemini API | People counting in the classroom photo, assignment review and comparison, video summary. |
| Browser camera / file picker | Scanning the QR code (`html5-qrcode`) and taking the classroom photo. |
| Hosting (Railway) | Public HTTPS deployment for the live demo; persistent volume for DB and files. |

### 2.2 User classes
| User | Description | Device |
|---|---|---|
| **Lecturer** | Creates courses, runs lectures, manages attendance, polls, summaries and assignments. | Laptop / projector (desktop UI), phone for the classroom photo. |
| **Student** | Joins courses, checks in, asks questions, votes, reads summaries, submits assignments. | Smartphone (mobile-first UI). |
| **Institution / system admin** | Supplies the list of authorized users (name, institutional email, role). | Offline (outside the app). |

### 2.3 Operating environment
- Any modern mobile or desktop browser (Chrome, Safari, Edge, Firefox). No app installation.
- Server: Python 3.12+, FastAPI, SQLAlchemy, SQLite (PostgreSQL-ready through SQLAlchemy).
- Camera-based QR scanning requires HTTPS (provided by the Railway deployment).

### 2.4 Design and implementation constraints
- **KISS** – one page, no build step, minimal dependencies.
- Only features that can actually be implemented and demoed in 10 minutes in class.
- **Privacy** – no ID numbers are stored or exported; users are identified by institutional email.
- The Gemini API key is configured only on the server (`GEMINI_API_KEY`), never in the client.

### 2.5 Assumptions and dependencies
- The institution provides the authorized user list in advance (no self sign-up).
- Students carry a smartphone with a camera and internet access.
- A valid Gemini API key with sufficient quota is available for the AI features. When it is missing, AI features report a clear "not configured" status and never invent results.

---

## 3. Functional Requirements

Priority: **M** = Must (needed for the demo), **S** = Should, **C** = Could.

### 3.1 Authentication and access (FR-1)
| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | The home screen shall let the user choose **Student login** or **Lecturer login**. | M |
| FR-1.2 | The user shall enter an institutional email; the system shall reject emails not in the institution's authorized list. | M |
| FR-1.3 | The system shall generate a one-time code (OTP) valid for **120 seconds** and show a countdown with a "resend code" option. | M |
| FR-1.4 | After a valid OTP the user shall be logged in with the role defined in the authorized list and redirected to "My Courses". | M |
| FR-1.5 | There shall be no self sign-up and no path that bypasses the OTP. | M |
| FR-1.6 | Every lecturer action shall be checked against course ownership; every student action against course membership. | M |

> **Demo note:** in the demo build the OTP is shown on screen (`debug_code`) instead of being emailed, so the demo does not depend on an SMTP server. In production the code is sent only by email.

### 3.2 Courses (FR-2)
| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | A lecturer shall create a course with a name and description; the system shall generate a unique Course ID. | M |
| FR-2.2 | A lecturer shall see the list of courses they teach, and may rename or delete a course. | M |
| FR-2.3 | A student shall join a course by entering its Course ID under "My Courses". | M |
| FR-2.4 | A student shall see the list of courses they belong to. | M |
| FR-2.5 | A lecturer shall see the course's student list and add or remove students manually. | M |
| FR-2.6 | The course screen shall show the active lecture (green), past lectures (grey) and the course assignments. | M |

### 3.3 Lectures (FR-3)
| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | A lecturer shall start a new lecture under a course. At most **one active lecture** per course is allowed. | M |
| FR-3.2 | Course members shall be notified when a lecture starts. | S |
| FR-3.3 | A lecturer shall close (end) the lecture; it then becomes a past lecture. Closing the lecture closes its live polls. | M |

### 3.4 Feature 1 – Smart attendance (FR-4) *(main feature)*
| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | When a lecture is active the lecturer's screen shall show a **dynamic QR code** that changes every **10 seconds**, with a progress bar. | M |
| FR-4.2 | The QR value shall be derived from a server secret (HMAC of lecture ID and time slot) so it cannot be predicted or reused later. | M |
| FR-4.3 | A student shall check in by scanning the QR code with the phone camera from inside their logged-in account. | M |
| FR-4.4 | A check-in shall be accepted only if: the lecture is active, the student is a member of the course, check-in is not locked, and the code is the current one (or the previous one within a **2-second** grace period). | M |
| FR-4.5 | A student can check in only once per lecture; a repeated scan shall return "already checked in" without creating a duplicate. | M |
| FR-4.6 | The lecturer shall see the live count and list of checked-in students. | M |
| FR-4.7 | The lecturer shall press **SESSION END** to lock check-ins; the lecture itself stays live (forum and polls continue). | M |
| FR-4.8 | After SESSION END the lecturer shall take a classroom photo (or upload one), from the laptop or from a phone through a one-time upload link/QR. | M |
| FR-4.9 | The system shall count the people in the photo using the AI vision model and show the count to the lecturer. JPEG, PNG, WebP and HEIC up to 12 MB are accepted. | M |
| FR-4.10 | The lecturer shall be able to correct the count manually. If AI counting fails, the system shall say so and ask for a manual count — it shall never invent a number. | M |
| FR-4.11 | **Cross-check – more check-ins than people:** the system shall warn about the discrepancy and offer three choices: (a) cancel and restart attendance (new round), (b) retake the photo, (c) approve the list and export. | M |
| FR-4.12 | **Cross-check – people ≥ check-ins:** the list is valid and can be approved. Students present who did not scan are responsible for that. | M |
| FR-4.13 | Restarting attendance shall delete only this lecture's check-ins and photo count; forum posts and polls are kept. | M |
| FR-4.14 | On approval the system shall generate an Excel file (`.xlsx`) with **Student Name, Institutional Email, Timestamp, Status** and **no ID numbers**. | M |
| FR-4.15 | The Excel report shall be downloadable by the lecturer at any time from the active or past lecture (online and offline use). | M |
| FR-4.16 | The student's check-in panel shall disappear after the student has checked in and the lecturer has locked attendance. | S |

### 3.5 Feature 2 – Lecture Q&A forum (FR-5)
| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | Every lecture shall have its own forum. | M |
| FR-5.2 | Course members shall post a question or suggestion during the lecture **and after it ended**. Empty posts are rejected. | M |
| FR-5.3 | The lecturer and other students shall reply in a thread under a post (1–3000 characters). | M |
| FR-5.4 | The lecturer shall be notified of new questions; the author shall be notified of replies. | S |

### 3.6 Feature 3 – KISS polls (FR-6)
| ID | Requirement | Priority |
|---|---|---|
| FR-6.1 | The lecturer shall create a multiple-choice poll with a question and 2–12 distinct options (up to 100 characters each), single or multiple answers. | M |
| FR-6.2 | Each poll shall show a **live results chart** and a **comment thread** under it. | M |
| FR-6.3 | **Live poll:** students vote while the lecture is active. Voting locks when the lecturer closes the poll or the lecture, whichever comes first. | M |
| FR-6.4 | **Post-lecture poll:** on a past lecture the lecturer shall set a time limit (1 minute – 7 days); voting is allowed only until it expires. | M |
| FR-6.5 | A student has one vote per poll (single-answer polls) and may change it while the poll is open. In multiple-answer polls each option toggles. | M |
| FR-6.6 | Only course members may vote or comment. | M |

### 3.7 Feature 4 – AI lecture summary (FR-7)
| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | From the lecture screen the lecturer shall either upload a lecture video (MP4, WebM, MOV, MPEG, AVI, WMV, 3GP, up to **500 MB**) or provide a link to the recording. | M |
| FR-7.2 | The summary shall run as a background job; the lecturer shall see its stage (sending, processing, summarizing, done/error). Only one job per lecture at a time. | M |
| FR-7.3 | The AI model shall produce a text summary keeping key topics, definitions and exercises; it is saved on the lecture. | M |
| FR-7.4 | All course students shall be able to read the summaries of all lectures; they shall be notified when a summary is ready. | M |
| FR-7.5 | Links currently supported directly are public YouTube links; recordings from Zoom / Google Classroom are downloaded and uploaded as a file. | S |

### 3.8 Feature 5 – Assignments and LLM review (FR-8)
| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | The lecturer shall create an assignment with title, description, due date, optional rubric and optional brief file; and may edit or delete it. | M |
| FR-8.2 | A student shall submit a file (PDF, DOCX, ZIP, source/text files, up to 50 MB). Resubmitting replaces the earlier submission. | M |
| FR-8.3 | On submission the LLM shall return a **recommended grade (0–100)** and a **deep review** (per-criterion scores, strengths, improvements), following the lecturer's rubric if given. | M |
| FR-8.4 | The grade shall be visible only to the student and the lecturer, and is **final only after lecturer approval**. The lecturer may change it. | M |
| FR-8.5 | The verbal review (without the grade) shall be published automatically to the course's **feedback forum**, anonymized as "Submission N". | M |
| FR-8.6 | The lecturer shall run an **LLM comparison** of all submissions (quality, strengths/weaknesses, similarity), visible **only to the lecturer**, with the average recommended grade and text-overlap indicators. | M |
| FR-8.7 | A failed AI review shall be retried automatically (after 20 s, 60 s, 180 s) and can be re-run by the lecturer. | S |
| FR-8.8 | The system shall not claim plagiarism; overlap figures are presented as indicators only. | M |

### 3.9 Notifications (FR-9)
| ID | Requirement | Priority |
|---|---|---|
| FR-9.1 | Users shall receive in-app notifications for new lectures, polls, forum replies, summaries, reviews and approved grades. | C |
| FR-9.2 | Users shall mark notifications as read (single, per course, all) and clear them. | C |

---

## 4. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Usability (KISS) | A student reaches check-in in at most 3 taps after login. The student UI is mobile-first; the lecturer UI is readable on a projector. |
| NFR-2 | Performance | QR check-in responds in under 1 s. Lecture data (attendance, forum, polls) refreshes on screen at most every 5 s. |
| NFR-3 | Performance | Photo counting returns within 60 s; assignment review within 120 s; video summaries run in the background without blocking the UI. |
| NFR-4 | Security | OTP and QR codes are compared in constant time; the QR secret is a server-side HMAC key; the Gemini key is server-side only. |
| NFR-5 | Security | All uploaded content (submissions, briefs) is treated by the LLM as untrusted data, not instructions (prompt-injection guard). |
| NFR-6 | Privacy | No national ID numbers are stored or exported. Grades are private to student and lecturer. The comparison report is lecturer-only. Classroom photos are not stored — only the count. |
| NFR-7 | Reliability | Gemini failures (429/5xx) are retried and fall back to a secondary model. The AI never fabricates a count, grade or summary. |
| NFR-8 | Portability | Runs locally (`uvicorn`) or on Railway; data folder configurable with `SMARTCLASS_DATA_DIR`; SQLite can be replaced by PostgreSQL. |
| NFR-9 | Maintainability | Backend split into data models (`models.py`), DB access (`database.py`) and API (`main.py`); automated tests with `pytest`. |
| NFR-10 | Compatibility | Works in current Chrome, Safari, Edge and Firefox on Android, iOS and desktop. |

---

## 5. Data Requirements

Main entities (see `Class Diagram.md` for the full diagram):

| Entity | Key data |
|---|---|
| User | email, name, role (lecturer / student) |
| Course | course_id, title, description, lecturer_email |
| StudentCourse | student_email, course_id |
| Session (lecture) | id, course_id, is_active, current_qr_code, ai_summary |
| AttendanceRecord | session_id, student_email, student_name, timestamp |
| SessionPhotoState / AttendanceApproval | detected_people, detection method, approval time, approved_with_discrepancy |
| Poll / PollVote / PollComment / PollTimeWindow | question, options, votes, comments, closes_at |
| ForumPost / ForumThreadReply | message, author, replies |
| Assignment / AssignmentBrief | title, description, due_date, rubric, brief file |
| Submission / SubmissionDocument | file, extracted text, llm_grade, llm_review, final_grade_approved, ai_status |
| AssignmentComparisonReport | report, generated_at |

Excel attendance report columns: `Student Name | Institutional Email | Timestamp | Status`.

---

## 6. Traceability to the Assignment

| Assignment feature | Requirements |
|---|---|
| 1. Attendance + photo count + spreadsheet (main) | FR-4.1 – FR-4.16 |
| 2. Comments / suggestions in real time and offline | FR-5.1 – FR-5.4 |
| 3. On-the-spot KISS polls | FR-6.1 – FR-6.6 |
| 4. ML summary of class video | FR-7.1 – FR-7.5 |
| 5. Deep LLM review of homework incl. comparison | FR-8.1 – FR-8.8 |
| KISS smartphone web app | NFR-1, NFR-10 |
| Real demo in class | NFR-8 (Railway HTTPS deployment) |
