from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_request_and_verify_otp():
    # 1. בקשת קוד OTP למייל מוסדי
    response = client.post("/api/auth/request-otp?email=student@ariel.ac.il")
    assert response.status_code == 200
    data = response.json()
    assert "debug_code" in data
    code = data["debug_code"]

    # 2. אימות הקוד שהתקבל
    verify_res = client.post(f"/api/auth/verify-otp?email=student@ariel.ac.il&code={code}")
    assert verify_res.status_code == 200
    user_data = verify_res.json()
    assert user_data["email"] == "student@ariel.ac.il"
    assert user_data["role"] == "student"

def test_create_course_and_session():
    # 1. יצירת קורס חדש על ידי מרצה
    course_res = client.post("/api/courses/create?title=Software%20Engineering&description=Testing%20Course&lecturer_email=lecturer@ariel.ac.il")
    assert course_res.status_code == 200
    course_data = course_res.json()
    course_id = course_data["course_id"]
    assert course_id is not None

    # 2. פתיחת שיעור חדש וקבלת קוד ה-QR
    session_res = client.post(f"/api/sessions/start?course_id={course_id}")
    assert session_res.status_code == 200
    session_data = session_res.json()
    assert "session_id" in session_data
    assert "qr_code" in session_data

    session_id = session_data["session_id"]
    qr_code = session_data["qr_code"]

    # 3. בדיקת דיווח נוכחות של סטודנט באמצעות סריקת ה-QR
    attendance_res = client.post(f"/api/attendance/scan?session_id={session_id}&student_email=student@ariel.ac.il&student_name=Yair%20Cohen&qr_code={qr_code}")
    assert attendance_res.status_code == 200
    assert attendance_res.json()["message"] == "Attendance recorded successfully"