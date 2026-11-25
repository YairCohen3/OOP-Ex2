# Technical Tools Report

We tested every tool on real data before choosing it: the class photos and the assignment examples the lecturer shared, real lecture recordings, and our own phones.

## 1. Counting people in the class photo
| Tool | Result |
|---|---|
| OpenCV (HOG) | Very light, but made for standing people. Missed many sitting or half-hidden students. |
| YOLOv8 | Good detection, but needs PyTorch. The server became heavy and slow to deploy. |
| **Gemini vision** ✓ | Counted sitting and far-away students well, and needs no extra libraries on our server. |

**Choice:** Gemini. Because any AI count can be wrong, the lecturer sees the number and can fix it. If the AI fails, the app asks for a manual count instead of guessing.

## 2. QR codes
- `qrcode` – creates the QR image on our server, so no outside service sees the codes.
- `html5-qrcode` – scans with the phone camera inside the browser. Worked on Android and iPhone.
- The code changes every 10 seconds, so a photo of the QR sent to a friend at home stops working.
- Problem we found: the phone camera works only over HTTPS. That is one reason we deployed to Railway.

## 3. Server
**FastAPI + SQLAlchemy + SQLite.** Easy to write, fast enough for a class, and has background tasks for long AI jobs. `openpyxl` creates the Excel attendance file.

## 4. AI for summaries and homework reviews
**Google Gemini API** (`gemini-3.5-flash`, with `gemini-3.5-flash-lite` as a backup).
- Homework: returns a grade, a review, strengths and things to improve. Follows the lecturer's rubric if there is one. We tested it on PDF, Word and ZIP files.
- Summaries: worked on recordings of 1–2 hours (up to 500 MB) using the Gemini Files API.
- Problem we found: Gemini is sometimes busy (errors 429/503). We added automatic retries and the backup model.

## 5. Hosting
**Railway.** Deploys on every push to GitHub and gives HTTPS.
Problem we found: without a Volume the database was deleted on every deploy, so we store the data on a Volume.

## Summary
| Need | Tool |
|---|---|
| Server | FastAPI, SQLite |
| Client | One HTML page, plain JavaScript |
| QR | qrcode, html5-qrcode |
| People counting, summaries, reviews | Gemini API |
| Excel | openpyxl |
| Hosting | Railway |
