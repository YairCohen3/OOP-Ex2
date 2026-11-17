from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import random
import openpyxl
from database import engine, Base, get_db
import models

# יצירת טבלאות מסד הנתונים אוטומטית
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartClass API", version="2.0")

# הגדרת CORS לתקשורת נוחה מול הדפדפן
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# זיכרון זמני לשמירת קודי ה-OTP
otp_storage = {}

# רשימת משתמשים מורשים מראש (Institutional Whitelist Onboarding)
ALLOWED_USERS_SEED = [
    {"email": "lecturer@ariel.ac.il", "name": "Dr. Boaz Lecturer", "role": "lecturer"},
    {"email": "student@ariel.ac.il", "name": "Yair Cohen", "role": "student"}
]


@app.on_event("startup")
def load_seed_users():
    db = next(get_db())
    for u_data in ALLOWED_USERS_SEED:
        existing = db.query(models.User).filter(models.User.email == u_data["email"]).first()
        if not existing:
            new_user = models.User(
                email=u_data["email"],
                name=u_data["name"],
                role=u_data["role"]
            )
            db.add(new_user)
    db.commit()
    db.close()


# --- 1. אימות ורישום מוסדי (Auth) ---
@app.post("/api/auth/request-otp")
def request_otp(email: str, db: Session = Depends(get_db)):
    # בדיקה האם המשתמש נמצא ברשימה המוסדית הסגורה
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Email is not registered in the institutional system."
        )

    code = str(random.randint(1000, 9999))
    otp_storage[email] = code

    print(f"\n================ [EMAIL DISPATCHER] ================")
    print(f"To: {email}")
    print(f"Subject: SmartClass - Institutional Verification Code (OTP)")
    print(f"Body: Hello {user.name}, your verification code is: {code}")
    print(f"====================================================\n")

    return {"message": "Email sent successfully to inbox", "debug_code": code}


@app.post("/api/auth/verify-otp")
def verify_otp(email: str, code: str, db: Session = Depends(get_db)):
    if email not in otp_storage or otp_storage[email] != code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    user = db.query(models.User).filter(models.User.email == email).first()
    return {"email": user.email, "name": user.name, "role": user.role}


# --- 2. ניהול קורסים והרשמה ---
@app.post("/api/courses/create")
def create_course(title: str, description: str, lecturer_email: str, db: Session = Depends(get_db)):
    # יצירת Course ID ייחודי אוטומטית כפי שהוגדר באפיון
    course_id = f"CRS-{random.randint(100, 999)}"
    new_course = models.Course(
        course_id=course_id,
        title=title,
        description=description,
        lecturer_email=lecturer_email
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return {"message": "Course created successfully", "course_id": course_id}


@app.get("/api/courses")
def get_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()


@app.post("/api/students/enroll")
def enroll_student(student_email: str, course_id: str, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.query(models.StudentCourse).filter(
        models.StudentCourse.student_email == student_email,
        models.StudentCourse.course_id == course_id
    ).first()

    if existing:
        return {"message": "You are already enrolled in this course"}

    enrollment = models.StudentCourse(student_email=student_email, course_id=course_id)
    db.add(enrollment)
    db.commit()
    return {"message": "Successfully enrolled in course!"}


@app.get("/api/students/{student_email}/courses")
def get_student_courses(student_email: str, db: Session = Depends(get_db)):
    enrollments = db.query(models.StudentCourse).filter(models.StudentCourse.student_email == student_email).all()
    course_ids = [e.course_id for e in enrollments]
    if not course_ids:
        return []
    return db.query(models.Course).filter(models.Course.course_id.in_(course_ids)).all()


# --- 3. ניהול שיעורים ו-QR דינמי ---
@app.post("/api/sessions/start")
def start_session(course_id: str, db: Session = Depends(get_db)):
    initial_qr = f"QR-{random.randint(10000, 99999)}"
    new_session = models.Session(
        course_id=course_id,
        is_active=True,
        current_qr_code=initial_qr
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"session_id": new_session.id, "course_id": course_id, "qr_code": initial_qr}


@app.get("/api/sessions/{session_id}/refresh-qr")
def refresh_qr(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == session_id, models.Session.is_active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    new_token = f"QR-{random.randint(10000, 99999)}"
    session.current_qr_code = new_token
    db.commit()
    return {"session_id": session.id, "qr_code": new_token}


# --- 4. דיווח נוכחות והצלבת YOLO ---
@app.post("/api/attendance/scan")
def scan_attendance(session_id: int, student_email: str, student_name: str, qr_code: str,
                    db: Session = Depends(get_db)):
    # 1. בדיקה שהשיעור קיים ופעיל
    session = db.query(models.Session).filter(models.Session.id == session_id, models.Session.is_active == True).first()
    if not session:
        raise HTTPException(status_code=400, detail="Session is not active or does not exist")

    # 2. ולידציה אקדמית: בדיקה שהסטודנט רשום לקורס של הסשן
    enrollment = db.query(models.StudentCourse).filter(
        models.StudentCourse.student_email == student_email,
        models.StudentCourse.course_id == session.course_id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=403, detail="Access denied: You are not enrolled in this course.")

    # 3. בדיקת תקינות קוד ה-QR המתחלף
    if session.current_qr_code != qr_code:
        raise HTTPException(status_code=400, detail="Invalid or expired QR code")

    # 4. מניעת כפילויות בדיווח
    existing = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session_id,
        models.AttendanceRecord.student_email == student_email
    ).first()

    if existing:
        return {"message": "Attendance already recorded for this session"}

    record = models.AttendanceRecord(session_id=session_id, student_email=student_email, student_name=student_name)
    db.add(record)
    db.commit()
    return {"message": "Attendance recorded successfully!"}


@app.post("/api/sessions/{session_id}/close-with-vision")
async def close_session_with_vision(session_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == session_id, models.Session.is_active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # סגירת הסשן (הפיכה לשיעור עבר באפור)
    session.is_active = False
    session.current_qr_code = None
    db.commit()

    # הדמיית ספירת YOLO לתמונת הכיתה
    scanned_count = db.query(models.AttendanceRecord).filter(models.AttendanceRecord.session_id == session_id).count()
    simulated_detected_people = scanned_count + random.randint(-1, 2)
    if simulated_detected_people < 0: simulated_detected_people = 0

    discrepancy = scanned_count > simulated_detected_people

    # הפקת קובץ Excel לתוצאות הנוכחות (שמירה על פרטיות: ללא תעודות זהות)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    ws.append(["Student Name", "Institutional Email", "Timestamp", "Status"])

    records = db.query(models.AttendanceRecord).filter(models.AttendanceRecord.session_id == session_id).all()
    for r in records:
        ws.append([r.student_name, r.student_email, str(r.timestamp), "Present"])

    filename = f"attendance_session_{session_id}.xlsx"
    wb.save(filename)

    return {
        "status": "Session closed successfully",
        "qr_scanned_count": scanned_count,
        "yolo_detected_people": simulated_detected_people,
        "discrepancy_detected": discrepancy,
        "warning": "Warning: More QR scans than detected people!" if discrepancy else "Attendance verified successfully.",
        "excel_report_generated": filename
    }


# --- 5. פורום שאלות והצעות ---
@app.post("/api/forum/post")
def post_forum_message(session_id: int, student_email: str, student_name: str, message: str,
                       db: Session = Depends(get_db)):
    post = models.ForumPost(session_id=session_id, student_email=student_email, student_name=student_name,
                            message=message)
    db.add(post)
    db.commit()
    return {"message": "Forum post created successfully"}


@app.post("/api/forum/reply")
def reply_forum_message(post_id: int, reply: str, db: Session = Depends(get_db)):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.reply = reply
    db.commit()
    return {"message": "Reply added successfully"}


@app.get("/api/sessions/{session_id}/forum")
def get_session_forum(session_id: int, db: Session = Depends(get_db)):
    return db.query(models.ForumPost).filter(models.ForumPost.id == session_id).all() if False else db.query(
        models.ForumPost).filter(models.ForumPost.session_id == session_id).all()


# --- 6. מערכת סקרים (KISS Polls) ---
@app.post("/api/polls/create")
def create_poll(session_id: int, question: str, options: str, db: Session = Depends(get_db)):
    poll = models.Poll(session_id=session_id, question=question, options=options, is_active=True)
    db.add(poll)
    db.commit()
    return {"message": "Poll created successfully", "poll_id": poll.id}


@app.post("/api/polls/vote")
def vote_poll(poll_id: int, student_email: str, selected_option: str, db: Session = Depends(get_db)):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id, models.Poll.is_active == True).first()
    if not poll:
        raise HTTPException(status_code=400, detail="Poll is closed or does not exist")

    # בדיקה האם הסשן של הסקר עדיין פעיל (במידה ומקושר לסשן)
    if poll.session_id:
        session = db.query(models.Session).filter(models.Session.id == poll.session_id).first()
        if session and not session.is_active:
            poll.is_active = False
            db.commit()
            raise HTTPException(status_code=400, detail="Poll is closed because the session has ended")

    existing_vote = db.query(models.PollVote).filter(
        models.PollVote.poll_id == poll_id,
        models.PollVote.student_email == student_email
    ).first()

    if existing_vote:
        existing_vote.selected_option = selected_option
    else:
        vote = models.PollVote(poll_id=poll_id, student_email=student_email, selected_option=selected_option)
        db.add(vote)

    db.commit()
    return {"message": "Vote recorded successfully"}


@app.get("/api/sessions/{session_id}/polls")
def get_session_polls(session_id: int, db: Session = Depends(get_db)):
    polls = db.query(models.Poll).filter(models.Poll.session_id == session_id).all()
    result = []
    for p in polls:
        votes = db.query(models.PollVote).filter(models.PollVote.poll_id == p.id).all()
        result.append({
            "poll_id": p.id,
            "question": p.question,
            "options": p.options.split(","),
            "is_active": p.is_active,
            "total_votes": len(votes)
        })
    return result


# --- 7. סיכומי הקלטת שיעור (AI Video Summary) ---
@app.post("/api/sessions/{session_id}/ai-summary")
def upload_ai_summary(session_id: int, summary_text: str, db: Session = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.ai_summary = summary_text
    db.commit()
    return {"message": "AI summary generated and saved successfully"}


@app.get("/api/sessions/{session_id}/ai-summary")
def get_ai_summary(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ai_summary": session.ai_summary or "No summary available yet."}


# --- 8. ניהול מטלות, בדיקת LLM ופורום משובים ---
@app.post("/api/assignments/create")
def create_assignment(course_id: str, title: str, description: str, due_date: str, db: Session = Depends(get_db)):
    assignment = models.Assignment(course_id=course_id, title=title, description=description, due_date=due_date)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return {"message": "Assignment created successfully", "assignment_id": assignment.id}


@app.get("/api/courses/{course_id}/assignments")
def get_course_assignments(course_id: str, db: Session = Depends(get_db)):
    return db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()


@app.post("/api/assignments/submit")
def submit_assignment(assignment_id: int, student_email: str, file_url: str, db: Session = Depends(get_db)):
    # סימולציית בדיקת LLM להפקת סקירה עמוקה וציון מומלץ
    simulated_review = "Deep AI Review: Code structure is clean and well-documented. Algorithmic efficiency is optimal (O(n log n)). Recommended to add edge case validation."
    simulated_grade = "92"

    sub = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id,
        models.Submission.student_email == student_email
    ).first()

    if sub:
        sub.file_url = file_url
        sub.llm_review = simulated_review
        sub.llm_grade = simulated_grade
    else:
        sub = models.Submission(
            assignment_id=assignment_id,
            student_email=student_email,
            file_url=file_url,
            llm_review=simulated_review,
            llm_grade=simulated_grade,
            final_grade_approved=False
        )
        db.add(sub)

    db.commit()
    return {"message": "Assignment submitted and reviewed by AI successfully", "llm_review": simulated_review,
            "llm_grade": simulated_grade}


@app.get("/api/assignments/{assignment_id}/submissions")
def get_assignment_submissions(assignment_id: int, db: Session = Depends(get_db)):
    return db.query(models.Submission).filter(models.Submission.assignment_id == assignment_id).all()


@app.post("/api/assignments/submission/{submission_id}/grade")
def update_or_approve_grade(submission_id: int, grade: str, approved: bool, db: Session = Depends(get_db)):
    sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.llm_grade = grade
    sub.final_grade_approved = approved
    db.commit()
    return {"message": "Grade updated and approval status saved successfully"}


@app.get("/api/assignments/{assignment_id}/feedback-forum")
def get_feedback_forum(assignment_id: int, db: Session = Depends(get_db)):
    # מציג את הסקירות המילוליות בלבד (ללא ציונים) ללמידת עמיתים כיתתית
    subs = db.query(models.Submission).filter(models.Submission.assignment_id == assignment_id).all()
    feedback_list = [{"student_email": s.student_email, "llm_review": s.llm_review} for s in subs if s.llm_review]
    return feedback_list


@app.get("/api/assignments/{assignment_id}/comparison")
def get_assignment_comparison(assignment_id: int, db: Session = Depends(get_db)):
    # ניתוח השוואתי למרצה בלבד
    subs = db.query(models.Submission).filter(models.Submission.assignment_id == assignment_id).all()
    total_subs = len(subs)
    return {
        "total_submissions": total_subs,
        "comparison_insights": f"AI Comparison Report: Analyzed {total_subs} submissions. Common strengths include clean syntax; potential plagiarism detected between 2 submissions. Average suggested grade is optimal."
    }
@app.get("/")
def serve_home():
    return FileResponse("index.html")