# SmartClass - Web-Based Teaching Management Tool

> A smart web application designed for lecturers and students to manage university classrooms effortlessly.

---

## Problem Statement
Current online tools used in university classrooms fail to provide a smooth, straightforward experience. Lecturers and students need simpler, smarter, and more direct tools to handle classroom presence, real-time engagement, and homework workflows without getting bogged down by cumbersome legacy portals.

---

## Our Approach
SmartClass offers a lightweight, end-to-end web platform built specifically for classroom environments. By removing complex external integrations and focusing on clean, mobile-first design for students and intuitive dashboards for lecturers, the platform streamlines the entire teaching and learning cycle.

---

## Key Features for Smarter Classroom Management

1. **Automated Attendance Tracking**
   * Students scan a dynamic QR code displayed on the classroom screen by the lecturer.
   * Following a session closure (`SESSION END`), the system cross-references QR scans with a physical head count of a classroom photo (Gemini vision, lecturer can correct it).
   * Generates a clean Excel attendance report ensuring student privacy by using institutional emails instead of ID numbers.

2. **Real-Time & Offline Q&A Forum**
   * A dedicated course forum where students can post questions or suggestions during the lecture or after hours.
   * Lecturers and peers can reply and collaborate seamlessly.

3. **Polls**
   * Multiple-choice questions created by the lecturer featuring a live-updating results graph and an interactive discussion thread.
   * Active during live classes or bounded by custom time limits for post-class reviews.

4. **AI Lecture Summarization**
   * Lecturers can upload a class recording or provide a link (Zoom / Google Classroom) to generate clear text summaries accessible to all students.

5. **Assignment Submissions & LLM Feedback**
   * Students submit homework and receive instant AI-generated deep reviews and recommended grades.
   * Final grades remain strictly private and subject to lecturer approval, while verbal feedback is published to a shared course feedback forum.

---

## Project Documents

| Document | Description |
|---|---|
| [Statement of Work](Documents/Statment%20of%20Work.md) | Objectives, scope, milestones |
| [Technical Tools Report](Documents/Technical%20Tools%20Report.md) | Tools tested and chosen |
| [SRS](Documents/SRS.md) | Functional and non-functional requirements |
| [Use Cases](Documents/Use%20Cases.md) | Actors, client stories, detailed use cases |
| [Components & Class Diagram](Documents/Class%20Diagram.md) | Architecture and low-level class diagram |
| [Sequence Diagrams](Documents/Sequence%20Diagrams.md) | Main flows step by step |
| [Testing Strategy](Documents/Testing%20Strategy.md) | Test levels, coverage per class, demo checklist |
| [Conclusion](Documents/Conclusion.md) | Results, decisions, limitations |

---

## Running Locally

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000   # open http://127.0.0.1:8000
python -m pytest -v                                               # run the tests
```

Set `GEMINI_API_KEY` to enable the AI features. More details (Hebrew): [README-SmartClass-HE.txt](README-SmartClass-HE.txt).

---

## How to Use the Platform

### For Lecturers:
1. **Log In:** Enter your institutional email and authenticate securely using the one-time verification code (OTP) sent to your inbox.
2. **Create a Course:** Click **"Create Course"**, enter the course name and description, and distribute the generated unique `Course ID` to your students.
3. **Manage Classes:** Open a new session at the beginning of class. Project the dynamic QR code for attendance, launch live polls, and post assignments.
4. **Post-Class Actions:** Upload recording links/videos for automated summaries, review student assignment submissions, and manage the Q&A forum.

### For Students:
1. **Log In:** Enter your institutional email and verify your identity using the OTP code sent to your email.
2. **Join a Course:** Go to **"My Courses"**, click **"Join Course"**, and enter the `Course ID` provided by your lecturer in class.
3. **During Class:** Scan the active attendance QR code to log your presence, participate in live polls, and ask questions in the course forum.
4. **Post-Class & Assignments:** Access lecture summaries, participate in offline polls before their timer expires, submit assignments, and review feedback.
