# SmartClass

A web app for running a class: attendance, questions, polls, lecture summaries and homework reviews.
The lecturer uses a laptop and projector, and students only need their phone (no app to install).

**Live site:** https://oop-ex2-production.up.railway.app

Ex2 – Introduction to Software Engineering
Yair Cohen ([@YairCohen3](https://github.com/YairCohen3)) & Yaari Meirovich ([@YaariMeirovich](https://github.com/YaariMeirovich))

## Demo video

*Coming soon.*

<!-- Replace with: [![SmartClass demo](thumbnail.png)](https://youtu.be/VIDEO_ID) -->

## The problem

The tools we use in class today are not good enough. Taking attendance wastes time and is easy to cheat, questions get lost, and homework feedback comes late. We wanted one simple tool that does all of this and uses AI where it actually helps.

## Features

1. **Attendance (main feature)** – students scan a QR code that changes every 10 seconds. The lecturer closes the check-in, takes one photo of the class, and Gemini counts the people. If there are more check-ins than people, the lecturer gets a warning. The final list is exported to Excel.
2. **Q&A forum** – every lecture has a forum, open during and after class.
3. **Polls** – quick polls with a live chart. Polls can also be opened after class with a time limit.
4. **Lecture summary** – upload the recording and Gemini writes a summary for the students.
5. **Homework review** – Gemini reviews the submission and suggests a grade. The lecturer approves it, and only then the student sees it. The lecturer can also compare all submissions.

**Not included:** Moodle / Zoom integration, sign-up, and storing ID numbers.

## Documents

| | |
|---|---|
| [SoW](Documents/Statement%20of%20Work.md) | Goal, scope and milestones |
| [Technical Tools Report](Documents/Technical%20Tools%20Report.md) | Tools we tried and what we chose |
| [SRS](Documents/SRS.md) | Requirements |
| [Use Cases & Components](Documents/Use%20Cases%20and%20Components.md) | Client stories, use cases, main components |
| [Class & Sequence Diagrams](Documents/Class%20and%20Sequence%20Diagrams.md) | Low-level design |
| [Testing Strategy](Documents/Testing%20Strategy.md) | How we test, and the demo checklist |


## Run it

```bash
pip install -r requirements.txt
uvicorn main:app --reload        # open http://127.0.0.1:8000
pytest -v                        # tests
```

For the AI features set `GEMINI_API_KEY`. On Railway also set `SMARTCLASS_DATA_DIR` to the Volume path so the data is not deleted on every deploy.

## Results

All five features work on the live site, and the attendance flow was tested with real phones and real class photos.
Main things we learned:
- Using Gemini for counting people was simpler and more accurate than YOLO / OpenCV.
- The AI can be wrong or busy, so the lecturer always has the final word (count, grades) and the app never makes up a result.
- Keeping it simple (one HTML file, one server file) let us change things fast.

Known limits: the login code is shown on screen for the demo (Live application will send an OTP via Email), the user list is in the code, and updates use polling every 5 seconds.

*Demo feedback: to be added after the presentation.*
