# Technical Tools Report & Real-World Testing

## 1. Objective & Scope
The purpose of this report is to evaluate and test the technical tools selected for the **SmartClass** application, ensuring they meet the KISS (Keep It Simple, Stupid) guidelines and perform reliably under real classroom conditions (specifically addressing attendance head-counting and AI processing workflows).

---

## 2. Tested Tools & Experimental Results

### A. Computer Vision & Attendance Cross-Checking
* **Tools tested:** OpenCV HOG person detector, YOLOv8, and the **Google Gemini vision model** (final choice).
* **Real-world test:** All three were run on the classroom photographs provided in the assignment folder (tiered lecture-hall seating, students with laptops and phones, partly hidden people).
* **Results & observations:**
  * *OpenCV HOG* – very light, but it is built for standing pedestrians and missed many seated and partly hidden students, so its count was only a rough estimate.
  * *YOLOv8* – much better detection of seated people, but it needs PyTorch and model weights. This made the server heavy to install and deploy (Railway build size and memory), which works against KISS.
  * *Gemini vision* – counted seated, partly hidden and distant people well, with no extra dependencies on our server (one API call). It is instructed not to count people on screens, posters or reflections.
* **Decision:** Gemini vision is used for the head count; OpenCV and YOLOv8 were removed from the code. Because any AI count can be wrong, the lecturer always sees the number and can correct it manually, and if the AI call fails the system asks for a manual count instead of inventing one.
* **Cross-check logic test:** when QR check-ins exceeded the head count, the lecturer got the discrepancy warning with the three options (restart attendance, retake the photo, or approve and export); when the head count was equal or higher, the list was approved, as defined in the spec.

### B. Dynamic QR & Mobile Scanning
* **Tools tested:** `qrcode[pil]` (server-side QR image), `html5-qrcode` (camera scanning in the phone browser).
* **Real-world test:** Students scanned the projected QR from Android and iPhone browsers.
* **Results & observations:**
  * The QR is generated on our own server, so attendance codes are not sent to a third-party QR service.
  * The code is an HMAC of the lecture ID and a 10-second time slot; a code photographed and sent outside the room stops working after 10 s (a 2-second grace period covers scans right at the change).
  * Mobile browsers open the camera only over **HTTPS**, so the demo runs on the Railway deployment; on a local network the photo can still be uploaded through a regular file picker.

### C. Backend & API Framework (Python FastAPI)
* **Tool tested:** FastAPI with SQLAlchemy (SQLite) and `openpyxl`.
* **Real-world test:** Simulated concurrent student check-ins via QR codes and automated `.xlsx` Excel report generation.
* **Results & observations:** Low latency, simple background tasks (video summaries, review retries), and clean generation of privacy-compliant attendance sheets (name, institutional email, timestamp, status — no ID numbers).

### D. LLM Integration for Assignment Reviews & Summarization (Google Gemini API)
* **Tool tested:** Gemini API (main model `gemini-3.5-flash`, fallback `gemini-3.5-flash-lite`; both configurable with environment variables) for video summaries, deep assignment reviews and comparative class analysis.
* **Real-world test:** Processed sample assignment submissions (PDF, DOCX, ZIP with source code) from the assignment list provided by the lecturer, and lecture recordings.
* **Results & observations:**
  * Reviews come back as structured JSON (score, criteria, strengths, improvements) and follow the lecturer's rubric when one is given.
  * Comparative analytics are visible **only** to the lecturer, while the verbal feedback (without grades) is published to the shared student forum.
  * Long lecture videos (1–2 hours, up to 500 MB) work through the Gemini Files API with low media resolution, run as a background job so the browser does not time out.
  * The model is sometimes busy (HTTP 429/503). Automatic retries and a fallback model were added; failed reviews are retried in the background after 20 s, 60 s and 180 s.
  * `gemini-2.5-flash`, named in the original spec, was shut down on 16/10/2026, so the default model was updated.

### E. Deployment (Railway)
* **Tool tested:** Railway with a persistent Volume (`SMARTCLASS_DATA_DIR`).
* **Results & observations:** Gives the public HTTPS URL needed for phone cameras. Without a Volume, SQLite and uploaded files are lost on redeploy, so the data folder is mounted on the Volume.

---

## 3. Conclusion & Integration Approval
All tested tools proved viable and lightweight. The main change from the original plan is replacing YOLOv8 with Gemini vision for head counting, which keeps the server simple and gave better counts on the class photos, with a manual correction as a safety net. The tools are approved for the final system composition and class demonstration.
