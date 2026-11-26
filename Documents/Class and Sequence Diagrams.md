# Class & Sequence Diagrams

## 1. Class diagram

### First version (before coding)
<img width="1691" height="3068" alt="First class diagram" src="https://github.com/user-attachments/assets/c85051a2-d4bf-4599-b86a-8a5ed758e681" />

### Final version (as implemented)
The core classes are in `models.py`. Classes we added later (photo count, approval, poll settings, lecture names…) are in `main.py`. We added them as new classes linked to the old ones instead of changing the old tables (Open/Closed principle).

<img width="4270" height="4593" alt="mermaid-diagram-2026-11-25-105702" src="https://github.com/user-attachments/assets/d7a2fc2f-d200-45cb-b632-0622033c0927" />


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
<img width="2974" height="2316" alt="mermaid-diagram-2026-11-25-104605" src="https://github.com/user-attachments/assets/47f60c5b-bb5d-4759-a966-928084c7bcb0" />


### Photo count and approval (main flow)

<img width="3166" height="3140" alt="mermaid-diagram-2026-11-25-104747" src="https://github.com/user-attachments/assets/46691ca2-68c1-46cd-b245-6b7ef0023c5c" />


### Lecture summary

<img width="2614" height="1732" alt="mermaid-diagram-2026-11-25-104821" src="https://github.com/user-attachments/assets/df6a4a41-a907-4457-bd3c-4e25dcfe73e5" />


### Homework review and grade

<img width="3494" height="2608" alt="mermaid-diagram-2026-11-25-104917" src="https://github.com/user-attachments/assets/c4286d76-4328-4de1-a722-eb1c57447b6c" />
