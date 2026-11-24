# Conclusion & Results: SmartClass

## 1. What We Built
SmartClass is a working, deployed web application (FastAPI + one responsive HTML page + SQLite, hosted on Railway over HTTPS) that covers all five features of the assignment:

| # | Feature | Result |
|---|---|---|
| 1 | **Smart attendance** (main) | Dynamic HMAC QR that changes every 10 s, phone check-in, SESSION END lock, classroom photo counted by Gemini vision with manual correction, cross-check with the three discrepancy options from the spec, and a privacy-safe Excel report (no ID numbers) available online and for download. |
| 2 | Q&A forum | One forum per lecture, threaded replies by lecturer and students, open during and after the lecture. |
| 3 | KISS polls | Single/multiple-answer polls, live bar chart, comment thread; live polls lock when the lecture or poll closes, post-lecture polls close after a lecturer-defined time. |
| 4 | AI lecture summary | Upload of recordings up to 500 MB (or a public link) summarized in the background by Gemini; summaries available to all course students. |
| 5 | Assignment review | Gemini deep review with per-criterion scores and a recommended grade, lecturer approval, anonymous feedback forum without grades, and a lecturer-only comparison report. |

## 2. Design Deliverables
| Assignment step | Document |
|---|---|
| 1. Repository, problem and scope | `README.md` |
| 2. Technical tools report | `Documents/Technical Tools Report.md` |
| 3. SoW | `Documents/Statment of Work.md` |
| 4. SRS | `Documents/SRS.md` |
| 5. Use cases / client stories | `Documents/Use Cases.md` |
| 6. Main software components | `Documents/Class Diagram.md` §1 |
| 7. Class and sequence diagrams | `Documents/Class Diagram.md` §2, `Documents/Sequence Diagrams.md` |
| 8. Testing strategy | `Documents/Testing Strategy.md`, `test_main.py` |
| 9. Demo application | `main.py`, `models.py`, `database.py`, `index.html` |

## 3. Main Decisions and What We Learned
- **KISS paid off.** A single HTML page with no build step and a single FastAPI file made it possible to change the UI and API quickly between test sessions and deploy in one push.
- **Design for wrong AI answers.** Every AI result is either confirmed by the lecturer (head count, grades) or shown as a recommendation. When the AI fails, the system says so and asks for a manual action — it never invents a count, a grade or a summary.
- **Replacing YOLOv8 with Gemini vision.** YOLOv8 gave good detections but made the deployment heavy; OpenCV HOG was light but missed seated students. Gemini vision kept the server simple and handled lecture-hall photos better, with manual correction as a safety net.
- **Real classroom constraints shaped the design.** Phone cameras need HTTPS (so we deployed to Railway), lecture videos are large (so we use the Gemini Files API and a background job), and AI services are sometimes busy (so we added retries and a fallback model).
- **Extending without breaking.** New needs (photo state, approval, poll time windows, comments, notifications) were added as new classes linked by foreign key, leaving the original tables unchanged — an application of the Open/Closed principle.
- **Privacy by design.** No ID numbers anywhere, grades private to student and lecturer, peer feedback anonymized, comparison visible only to the lecturer, classroom photo not stored.

## 4. Limitations and Future Work
- OTP is shown on screen in the demo; production should send it by email and use a session token instead of passing the email with each request.
- The authorized user list is in the code; it should be imported from the institution's file.
- Live updates use 5-second polling; WebSockets would make polls and forum truly real-time.
- Direct recording links are limited to public YouTube; Zoom / Google Classroom integration was out of scope.
- A few minor permission gaps found while writing the tests are listed in `Testing Strategy.md` §9.
- SQLite is enough for one class; PostgreSQL would be used for an institution (SQLAlchemy makes the switch small).

## 5. Demo in Class
The demo follows the checklist in `Testing Strategy.md` §6 (about 10 minutes): login → course → live lecture with QR check-in from students' phones → SESSION END and classroom photo → cross-check and Excel → forum and live poll → lecture summary → assignment review and comparison.

*Demo outcome and class feedback: to be added after the presentation.*
