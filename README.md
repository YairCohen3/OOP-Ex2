# SmartClass – Web-Based Teaching Tool

SmartClass is a web app for running a university class: attendance, questions, polls, lecture summaries and assignment reviews. Lecturers work from a laptop and a projector, and students use their phones with no app to install.

**Live demo:** https://oop-ex2-production.up.railway.app
**Course:** Introduction to Software Engineering (OOP, OOD), Ex2: Vibe Coding & Deep Designing
**Team:** Yair Cohen ([@YairCohen3](https://github.com/YairCohen3)), Yaari Meirovich ([@YaariMeirovich](https://github.com/YaariMeirovich))

---

## Problem statement

The online tools used in class today are slow and awkward. Taking attendance by calling names wastes class time and is easy to fake. Questions get lost, quick polls need a separate tool, recordings sit unwatched, and homework feedback arrives late. Lecturers and students need simpler, LLM-ready tools.

## Scope

**In scope:** the five features in the assignment, in one web app that runs in this class:

| # | Feature | What SmartClass does |
|---|---|---|
| 1 | **Attendance** (main feature) | Students check in by scanning a QR code that changes every 10 seconds. The lecturer locks check-ins, takes one classroom photo, Gemini counts the people, and the system cross-checks the count against the check-ins. The approved list is exported to Excel (no ID numbers). |
| 2 | **Q&A forum** | A forum for each lecture, open during and after class, with threaded replies. |
| 3 | **Polls** | Quick multiple-choice polls with a live chart and a discussion thread. Live polls close with the lecture; polls on past lectures close after a time limit. |
| 4 | **Lecture summary** | The lecturer uploads the recording (up to 500 MB) or a public YouTube link, and Gemini writes a summary that all students can read. |
| 5 | **Assignment review** | Students submit their work, Gemini writes a deep review and recommends a grade, and the lecturer approves or changes it. Students see the grade only after approval. Anonymous feedback is shared with the class, and a comparison of all submissions is shown to the lecturer only. |

**Out of scope** (per the assignment guidelines): integration with Moodle, Zoom or personal-information systems, self sign-up, and production identity management.

---

## Project documents

Each item in the assignment's To-Do list and where it is answered:

| To-Do | Deliverable | Document |
|---|---|---|
| 1 | Repository, problem and scope | This README |
| 3 | Technical tools report | [Technical Tools Report](Documents/Technical%20Tools%20Report.md) |
| 4 | Statement of Work | [Statement of Work](Documents/Statement%20of%20Work.md) |
| 5 | Software Requirements Specification | [SRS](Documents/SRS.md) |
| 6 | Use cases and client stories | [Use Cases](Documents/Use%20Cases.md) |
| 7 | Main software components | [Components & Class Diagram](Documents/Class%20Diagram.md), section 1 |
| 8 | Class and sequence diagrams | [Class Diagram](Documents/Class%20Diagram.md), section 2, and [Sequence Diagrams](Documents/Sequence%20Diagrams.md) |
| 9 | Testing strategy | [Testing Strategy](Documents/Testing%20Strategy.md) and [`test_main.py`](test_main.py) |
| 10 | Demo web application | The code in this repository, deployed at the live demo link |
| 11 | Demo in class | Demo script in [Testing Strategy](Documents/Testing%20Strategy.md), section 6 |
| 12 | Conclusion | [Conclusion](Documents/Conclusion.md) |

---

## Technology

| Part | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| Frontend | One HTML page with plain JavaScript and CSS (no build step), mobile-first, Hebrew and English |
| AI | Google Gemini API: people counting, video summaries, assignment reviews and comparison |
| QR | `qrcode` (generated on our server), `html5-qrcode` (phone camera scanning) |
| Files | `openpyxl` (Excel report), `pypdf` and `python-docx` (reading submissions), `Pillow` (photos) |
| Hosting | Railway, with a persistent Volume for the database and uploaded files |
| Tests | `pytest` with FastAPI `TestClient` |

## Repository structure

```
├── main.py            FastAPI app: all API endpoints and business logic
├── models.py          Core database classes (SQLAlchemy)
├── database.py        Database connection and data folder
├── index.html         The whole web interface (lecturer and student)
├── test_main.py       Automated tests (unit and API)
├── conftest.py        Test setup: temporary database, no AI calls
├── requirements.txt   Python dependencies
├── README.he.md       Run and deploy guide in Hebrew
└── Documents/         Design documents (SoW, SRS, use cases, diagrams, tests, conclusion)
```

---

## Running locally

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000   # then open http://127.0.0.1:8000
python -m pytest -v                                               # run the tests
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | For the AI features | Without it, the AI features say they are not configured. They never invent a result. |
| `GEMINI_MODEL` | No | Main model. Default: `gemini-3.5-flash` |
| `GEMINI_FALLBACK_MODEL` | No | Used when the main model is busy. Default: `gemini-3.5-flash-lite` |
| `SMARTCLASS_DATA_DIR` | On Railway | Folder for the database, uploads and Excel reports. Point it to the Volume (for example `/data`), or data is lost on every deploy. |
| `SMARTCLASS_QR_SECRET` | With more than one server | Fixed secret for the dynamic QR codes. |

The API key is set only on the server. It is never in the code or in the browser.

### Deploying (Railway)

1. Push to `master`. Railway deploys automatically.
2. Add a Volume and set `SMARTCLASS_DATA_DIR` to its mount path.
3. Set `GEMINI_API_KEY` under Variables.

The phone camera needs HTTPS to scan the QR, which the Railway deployment provides.

---

## How to use

### Lecturer
1. **Log in** with your institutional email and the one-time code. Your role comes from the institution's list.
2. **Create a course** and give students the Course ID (`CRS-…`).
3. **Start a lecture.** The attendance QR fills the screen for the projector. When the students have checked in, press **End attendance**.
4. **Take a classroom photo** (on the laptop, or on your phone through the upload QR). Gemini counts the people. Check the cross-check result and press **Approve & export Excel**.
5. **During and after the lecture:** answer questions, run polls, and generate the summary from the recording.
6. **Assignments:** publish an assignment, read the AI reviews, and approve or change each grade. You can also run the AI comparison of all submissions.

### Student
1. **Log in** with your institutional email and the one-time code.
2. **Join a course** with the Course ID from your lecturer.
3. **In class:** open the live lecture, scan the QR to check in, ask questions and vote in polls.
4. **After class:** read the lecture summary and submit assignments. Your grade and feedback appear after your lecturer approves them.

---

## Known limitations

- For the demo, the one-time login code is shown on screen instead of being sent by email.
- The list of authorized users is defined in the code (`AUTH_USERS` in `main.py`).
- Live updates refresh every 5 seconds (polling), not over WebSockets.

The full list is in the [Conclusion](Documents/Conclusion.md).
