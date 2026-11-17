# System Architecture & UML Diagrams

## 1. Main Software Components
The SmartClass application is composed of several decoupled modules to ensure maintainability and adherence to the KISS principle:

1. **Client Application (React/Tailwind):**
   * *Student App:* Mobile-first interface for QR scanning, poll voting, forum participation, and assignment submission.
   * *Lecturer Dashboard:* Desktop-optimized interface for session management, QR projection, photo upload, and comparative analytics viewing.
2. **API Gateway & Core Logic (Python FastAPI):**
   * *Auth Service:* Handles institutional email verification and OTP generation.
   * *Course & Session Manager:* Manages course creation, enrollment, and live session states.
   * *Collaboration Engine:* Manages the real-time/offline Q&A forum and live-updating KISS polls.
3. **Attendance & Vision Engine:**
   * Generates dynamic QR codes.
   * Integrates with **YOLOv8** to process classroom photos and return physical headcounts.
   * Executes the cross-referencing logic and generates `.xlsx` reports via `openpyxl`.
4. **AI & LLM Service:**
   * Integrates with **Google Gemini API**.
   * Processes assignment submissions to generate deep reviews and comparative analysis.
   * Processes video files/links to generate lecture text summaries.
5. **Database Layer (PostgreSQL/SQLite):** Stores relational data (Users, Courses, Sessions, Logs).

---

## 2. Low-Level Class Diagram
*Note: This diagram illustrates the core Object-Oriented Design (OOD) of the system.*

<img width="1691" height="3068" alt="mermaid-diagram-2026-11-16-194058" src="https://github.com/user-attachments/assets/c85051a2-d4bf-4599-b86a-8a5ed758e681" />
