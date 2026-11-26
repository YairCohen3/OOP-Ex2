# Statement of Work (SoW)

## Goal
Build and demo SmartClass, a simple web app for teaching in class (KISS). It should work in our real class, with students using their phones.

## Scope
**In scope:**
- Attendance with a dynamic QR, a classroom photo counted by AI, and an Excel report (main feature)
- Q&A forum per lecture
- Quick polls with live results
- AI summary of a lecture recording
- AI review of homework, with lecturer approval and a comparison between students

**Out of scope:**
- Integration with Moodle, Zoom or the university systems
- Self sign-up (users come from a list given by the institution)
- Storing ID numbers

## Deliverables
1. GitHub repo with README (problem and scope)
2. Technical tools report
3. SoW (this document) and SRS
4. Use cases and main components
5. Class and sequence diagrams
6. Testing strategy and tests
7. Working web app, deployed online
8. 10-minute demo in class

## Milestones
| # | Milestone | Done |
|---|---|---|
| 1 | Repo, problem definition, README, SoW | ✓ |
| 2 | Tools report, components and diagrams | ✓ |
| 3 | SRS and testing strategy | ✓ |
| 4 | Working app on Railway | ✓ |
| 5 | Demo in class and conclusion | 07/12/2026 |

## Team
Yair Cohen and Yaari Meirovich.

## Assumptions
- Students have a smartphone with a camera and internet.
- We have a Gemini API key for the AI features.
- The app runs over HTTPS (needed for the phone camera).
