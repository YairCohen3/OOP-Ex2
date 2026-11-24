# Software Requirements Specification (SRS)

## 1. Introduction
SmartClass is a web app for lecturers and students. It covers attendance, a Q&A forum, polls, lecture summaries and homework reviews. Students use it on their phone, the lecturer on a laptop with a projector.

**Users**
- **Lecturer** – creates courses, runs lectures, approves attendance and grades.
- **Student** – joins courses, checks in, asks questions, votes, submits homework.

**Priority:** M = must have, S = should have.

## 2. Functional requirements

### Login and courses
| ID | Requirement | P |
|---|---|---|
| FR-1 | Login with institutional email and a one-time code (valid for 120 s). Only emails from the institution's list can log in. The role comes from the list. | M |
| FR-2 | A lecturer creates a course and gets a Course ID. Students join with this ID. | M |
| FR-3 | A lecturer can rename or delete a course and add or remove students. | S |
| FR-4 | A lecturer starts a lecture (only one live lecture per course) and ends it. After ending, they return to the course page. | M |
| FR-5 | A lecturer can rename a lecture and delete a past lecture. | S |

### Feature 1 – Attendance (main)
| ID | Requirement | P |
|---|---|---|
| FR-6 | When a lecture starts, a QR code opens full screen. It changes every 10 seconds and stays on screen until the lecturer presses "End attendance". | M |
| FR-7 | A student checks in by scanning the QR from their account. Only course students, only once, and only with the current code. | M |
| FR-8 | The lecturer sees the live number and list of students who checked in. | M |
| FR-9 | "End attendance" locks the check-in. The lecturer can reopen it before approving. | M |
| FR-10 | The lecturer takes or uploads a class photo (from the laptop or the phone). Gemini counts the people, and the lecturer can fix the number. | M |
| FR-11 | If there are more check-ins than people, show a warning with 3 options: restart attendance, retake the photo, or approve anyway. | M |
| FR-12 | If people ≥ check-ins, the list is valid and can be approved. | M |
| FR-13 | After approval, create an Excel file: name, email, time, status. No ID numbers. It can be downloaded later too. | M |

### Feature 2 – Q&A forum
| ID | Requirement | P |
|---|---|---|
| FR-14 | Each lecture has a forum. Course members can post during and after the lecture. | M |
| FR-15 | The lecturer and students can reply to a post. | M |

### Feature 3 – Polls
| ID | Requirement | P |
|---|---|---|
| FR-16 | The lecturer creates a poll with 2–12 options (one or multiple answers). | M |
| FR-17 | Students vote and everyone sees a live chart. Each poll has a comment thread. | M |
| FR-18 | A live poll closes when the lecturer closes it or ends the lecture. A poll on a past lecture closes after a time limit the lecturer sets. | M |

### Feature 4 – Lecture summary
| ID | Requirement | P |
|---|---|---|
| FR-19 | The lecturer uploads a recording (up to 500 MB) or a YouTube link, and Gemini writes a summary in the background. | M |
| FR-20 | The lecturer can edit the summary. All course students can read it. | M |

### Feature 5 – Homework review
| ID | Requirement | P |
|---|---|---|
| FR-21 | The lecturer creates, edits and deletes assignments (title, instructions, due date, optional rubric and file). | M |
| FR-22 | A student submits up to 10 files (50 MB total). Submitting again replaces the old submission. | M |
| FR-23 | Gemini reviews the submission and suggests a grade. Only the lecturer sees them at first. | M |
| FR-24 | The lecturer approves or changes the grade. Until then the student sees "Waiting for your lecturer's grade". | M |
| FR-25 | After approval, the review (without grade or name) is shown to the class in a feedback forum. | M |
| FR-26 | The lecturer can run an AI comparison of all submissions. Only the lecturer sees it. | M |

### Other
| ID | Requirement | P |
|---|---|---|
| FR-27 | In-app notifications (new lecture, reply, summary, grade). | S |
| FR-28 | The interface works in English and Hebrew. | S |

## 3. Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-1 | **Simple:** a student gets to check-in in 3 taps or less. Works in any phone browser, no install. |
| NFR-2 | **Fast:** check-in answers in under 1 second. Screens update every 5 seconds. |
| NFR-3 | **Privacy:** no ID numbers. Grades are seen only by the student and the lecturer. Class photos are not saved, only the count. |
| NFR-4 | **Security:** every lecturer action checks that it is the course's lecturer. The QR is signed by the server. The API key is only on the server. |
| NFR-5 | **AI honesty:** if the AI fails, the app says so. It never makes up a count, grade or summary. |
| NFR-6 | **Runs anywhere:** locally or on Railway, over HTTPS. |
