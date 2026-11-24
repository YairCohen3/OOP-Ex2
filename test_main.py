"""SmartClass automated tests (pytest).

Run from the project folder:
    python -m pytest -v

conftest.py points the app at an empty temporary database, so these tests never
touch the real smartclass.db. Gemini is not configured during the tests, so the
AI features are tested for their "not configured" behaviour (no invented results).

Structure (see Documents/Testing Strategy.md):
    1. Unit tests      – pure logic: QR codes, attendance cross-check, poll options
    2. API tests       – one group per feature / class
"""
import io
import time

import openpyxl
import pytest
from fastapi.testclient import TestClient

import main
import models
from database import SessionLocal

LECTURER = "ohadbennun25@gmail.com"   # lecturer in main.AUTH_USERS
STUDENT = "yair18487@gmail.com"       # student in main.AUTH_USERS
STUDENT_2 = "student2@test.ac.il"     # extra course member used for privacy tests
OUTSIDER = "outsider@test.ac.il"      # not a member of any course


# ---------------------------------------------------------------- fixtures & helpers

@pytest.fixture(scope="module")
def client():
    # The context manager runs the startup event, which seeds the authorized users.
    with TestClient(main.app) as test_client:
        yield test_client


def make_course(client, title="Software Engineering"):
    response = client.post("/api/courses/create",
                           params={"title": title, "description": "Test course", "lecturer_email": LECTURER})
    assert response.status_code == 200, response.text
    return response.json()["course_id"]


def enroll(client, course_id, email=STUDENT):
    response = client.post("/api/students/enroll", params={"student_email": email, "course_id": course_id})
    assert response.status_code == 200, response.text


def start_lecture(client, course_id):
    response = client.post("/api/sessions/start", params={"course_id": course_id, "lecturer_email": LECTURER})
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def scan(client, session_id, email=STUDENT, name="Yair Cohen", qr=None):
    qr = qr or main.get_qr_status(session_id)["qr_code"]
    return client.post("/api/attendance/scan", params={
        "session_id": session_id, "student_email": email, "student_name": name, "qr_code": qr})


def set_people_count(client, session_id, people):
    response = client.post(f"/api/sessions/{session_id}/photo/manual-count",
                           params={"lecturer_email": LECTURER, "people": people})
    assert response.status_code == 200, response.text
    return response.json()


def close_lecture(client, session_id):
    response = client.post(f"/api/sessions/{session_id}/close",
                           params={"lecturer_email": LECTURER, "approve_mismatch": True})
    assert response.status_code == 200, response.text


@pytest.fixture
def live_lecture(client):
    """A course with STUDENT and STUDENT_2 enrolled and an active lecture."""
    course_id = make_course(client)
    enroll(client, course_id, STUDENT)
    enroll(client, course_id, STUDENT_2)
    return course_id, start_lecture(client, course_id)


# ================================================================ 1. UNIT TESTS

class TestFreshStart:
    def test_runs_once_and_ends_live_lectures(self, client):
        course_id = make_course(client)
        enroll(client, course_id)
        session_id = start_lecture(client, course_id)
        db = SessionLocal()
        try:
            db.query(main.MaintenanceRun).delete()
            db.commit()
            main.run_fresh_start_once(db)
            assert db.query(models.Session).filter(models.Session.id == session_id).first().is_active is False
            assert db.query(models.StudentCourse).filter(models.StudentCourse.student_email == STUDENT).count() == 0
            # A second run changes nothing (marker already stored)
            new_lecture = models.Session(course_id=course_id, is_active=True)
            db.add(new_lecture)
            db.commit()
            main.run_fresh_start_once(db)
            assert db.query(models.Session).filter(models.Session.id == new_lecture.id).first().is_active is True
        finally:
            db.close()


class TestQRCode:
    def test_format_is_qr_and_8_digits(self):
        code = main.qr_at(1, 100)
        assert code.startswith("QR-") and len(code) == 11 and code[3:].isdigit()

    def test_same_lecture_and_slot_gives_same_code(self):
        assert main.qr_at(7, 500) == main.qr_at(7, 500)

    def test_code_changes_every_slot_and_per_lecture(self):
        assert main.qr_at(7, 500) != main.qr_at(7, 501)
        assert main.qr_at(7, 500) != main.qr_at(8, 500)

    def test_status_reports_10_second_period(self):
        status = main.get_qr_status(1)
        assert status["period_seconds"] == 10
        assert 0 < status["expires_in_seconds"] <= 10


class TestAttendanceCrossCheck:
    def test_no_photo_yet(self):
        assert main.attendance_crosscheck(5, None)["status"] == "no_photo"

    def test_more_checkins_than_people_is_a_discrepancy(self):
        result = main.attendance_crosscheck(10, 7)
        assert result["status"] == "more_checkins"
        assert result["difference"] == 3

    def test_more_people_than_checkins_is_valid(self):
        result = main.attendance_crosscheck(7, 10)
        assert result["status"] == "more_people"
        assert result["difference"] == 3

    def test_equal_counts_match(self):
        assert main.attendance_crosscheck(8, 8)["status"] == "match"

    def test_empty_class(self):
        assert main.attendance_crosscheck(0, 0)["status"] == "match"


class TestPollChoices:
    def test_json_options_may_contain_commas(self):
        poll = models.Poll(options='["Yes, sure", "No"]')
        assert main.poll_choices(poll) == ["Yes, sure", "No"]

    def test_old_comma_separated_options(self):
        assert main.poll_choices(models.Poll(options="A, B ,C")) == ["A", "B", "C"]

    def test_empty_options(self):
        assert main.poll_choices(models.Poll(options="")) == []


# ================================================================ 2. API TESTS

class TestAuthentication:
    def test_request_and_verify_otp(self, client):
        response = client.post("/api/auth/request-otp", params={"email": STUDENT})
        assert response.status_code == 200
        data = response.json()
        assert data["expires_in_seconds"] == 120
        verify = client.post("/api/auth/verify-otp", params={"email": STUDENT, "code": data["debug_code"]})
        assert verify.status_code == 200
        assert verify.json() == {"email": STUDENT, "name": "Yair Cohen", "role": "student"}

    def test_lecturer_gets_lecturer_role(self, client):
        code = client.post("/api/auth/request-otp", params={"email": LECTURER}).json()["debug_code"]
        user = client.post("/api/auth/verify-otp", params={"email": LECTURER, "code": code}).json()
        assert user["role"] == "lecturer"

    def test_unknown_email_is_rejected(self, client):
        assert client.post("/api/auth/request-otp", params={"email": OUTSIDER}).status_code == 403

    def test_wrong_code_is_rejected(self, client):
        code = client.post("/api/auth/request-otp", params={"email": STUDENT}).json()["debug_code"]
        wrong = "0000" if code != "0000" else "1111"
        assert client.post("/api/auth/verify-otp", params={"email": STUDENT, "code": wrong}).status_code == 401

    def test_code_can_be_used_only_once(self, client):
        code = client.post("/api/auth/request-otp", params={"email": STUDENT}).json()["debug_code"]
        assert client.post("/api/auth/verify-otp", params={"email": STUDENT, "code": code}).status_code == 200
        assert client.post("/api/auth/verify-otp", params={"email": STUDENT, "code": code}).status_code == 401

    def test_expired_code_is_rejected(self, client):
        code = client.post("/api/auth/request-otp", params={"email": STUDENT}).json()["debug_code"]
        main.otp_store[STUDENT]["expires_at"] = time.time() - 1
        assert client.post("/api/auth/verify-otp", params={"email": STUDENT, "code": code}).status_code == 401


class TestCourses:
    def test_create_course_generates_unique_id(self, client):
        first, second = make_course(client), make_course(client)
        assert first.startswith("CRS-") and first != second

    def test_empty_course_name_is_rejected(self, client):
        response = client.post("/api/courses/create",
                               params={"title": "  ", "description": "", "lecturer_email": LECTURER})
        assert response.status_code == 400

    def test_student_cannot_create_course(self, client):
        response = client.post("/api/courses/create",
                               params={"title": "X", "description": "", "lecturer_email": STUDENT})
        assert response.status_code == 403

    def test_student_joins_course_with_course_id(self, client):
        course_id = make_course(client)
        enroll(client, course_id)
        courses = client.get(f"/api/students/{STUDENT}/courses").json()
        assert course_id in [course["course_id"] for course in courses]

    def test_join_unknown_course_fails(self, client):
        response = client.post("/api/students/enroll", params={"student_email": STUDENT, "course_id": "CRS-0"})
        assert response.status_code == 404

    def test_lecturer_adds_and_removes_student(self, client):
        course_id = make_course(client)
        add = client.post(f"/api/courses/{course_id}/students",
                          params={"lecturer_email": LECTURER, "student_email": STUDENT})
        assert add.status_code == 200
        students = client.get(f"/api/courses/{course_id}/students", params={"lecturer_email": LECTURER}).json()
        assert [s["email"] for s in students] == [STUDENT]
        remove = client.delete(f"/api/courses/{course_id}/students/{STUDENT}", params={"lecturer_email": LECTURER})
        assert remove.status_code == 200

    def test_only_the_course_lecturer_manages_students(self, client):
        course_id = make_course(client)
        response = client.get(f"/api/courses/{course_id}/students", params={"lecturer_email": STUDENT})
        assert response.status_code == 403


class TestLectures:
    def test_start_lecture_returns_qr(self, client):
        course_id = make_course(client)
        response = client.post("/api/sessions/start", params={"course_id": course_id, "lecturer_email": LECTURER})
        assert response.status_code == 200
        assert "session_id" in response.json() and response.json()["qr_code"].startswith("QR-")

    def test_only_one_active_lecture_per_course(self, client):
        course_id = make_course(client)
        first = start_lecture(client, course_id)
        again = client.post("/api/sessions/start", params={"course_id": course_id, "lecturer_email": LECTURER}).json()
        assert again["session_id"] == first and again["already_active"] is True

    def test_student_cannot_start_lecture(self, client):
        course_id = make_course(client)
        response = client.post("/api/sessions/start", params={"course_id": course_id, "lecturer_email": STUDENT})
        assert response.status_code == 403

    def test_close_requires_photo_count_or_explicit_approval(self, client, live_lecture):
        _, session_id = live_lecture
        scan(client, session_id)
        response = client.post(f"/api/sessions/{session_id}/close", params={"lecturer_email": LECTURER})
        assert response.status_code == 409

    def test_lecture_with_no_check_ins_closes_without_photo(self, client, live_lecture):
        _, session_id = live_lecture
        response = client.post(f"/api/sessions/{session_id}/close", params={"lecturer_email": LECTURER})
        assert response.status_code == 200
        assert response.json()["qr_scanned_count"] == 0

    def test_closed_lecture_becomes_past(self, client, live_lecture):
        course_id, session_id = live_lecture
        close_lecture(client, session_id)
        sessions = client.get(f"/api/courses/{course_id}/sessions").json()
        assert sessions[0]["id"] == session_id and sessions[0]["is_active"] is False


class TestDeleteLecture:
    def test_lecturer_deletes_past_lecture_with_its_data(self, client, live_lecture):
        course_id, session_id = live_lecture
        scan(client, session_id)
        client.post("/api/forum/post", params={"session_id": session_id, "student_email": STUDENT,
                                               "student_name": "Yair Cohen", "message": "Question"})
        client.post("/api/polls/create", params={"session_id": session_id, "question": "Q?",
                                                 "options": '["A", "B"]', "lecturer_email": LECTURER})
        set_people_count(client, session_id, 5)
        close_lecture(client, session_id)
        response = client.delete(f"/api/sessions/{session_id}", params={"lecturer_email": LECTURER})
        assert response.status_code == 200
        assert session_id not in [s["id"] for s in client.get(f"/api/courses/{course_id}/sessions").json()]
        db = SessionLocal()
        try:
            assert db.query(models.AttendanceRecord).filter(models.AttendanceRecord.session_id == session_id).count() == 0
            assert db.query(models.Poll).filter(models.Poll.session_id == session_id).count() == 0
            assert db.query(models.ForumPost).filter(models.ForumPost.session_id == session_id).count() == 0
        finally:
            db.close()

    def test_live_lecture_cannot_be_deleted(self, client, live_lecture):
        _, session_id = live_lecture
        response = client.delete(f"/api/sessions/{session_id}", params={"lecturer_email": LECTURER})
        assert response.status_code == 409

    def test_student_cannot_delete_lecture(self, client, live_lecture):
        _, session_id = live_lecture
        close_lecture(client, session_id)
        response = client.delete(f"/api/sessions/{session_id}", params={"lecturer_email": STUDENT})
        assert response.status_code == 403


class TestAttendanceCheckIn:
    def test_student_checks_in_with_current_qr(self, client, live_lecture):
        _, session_id = live_lecture
        response = scan(client, session_id)
        assert response.status_code == 200
        assert response.json()["already_checked_in"] is False

    def test_second_scan_does_not_duplicate(self, client, live_lecture):
        _, session_id = live_lecture
        scan(client, session_id)
        assert scan(client, session_id).json()["already_checked_in"] is True
        state = client.get(f"/api/sessions/{session_id}/live-state", params={"lecturer_email": LECTURER}).json()
        assert state["checked_in_count"] == 1

    def test_old_qr_code_is_rejected(self, client, live_lecture):
        _, session_id = live_lecture
        old_slot = int(time.time() // main.QR_TTL_SECONDS) - 5
        response = scan(client, session_id, qr=main.qr_at(session_id, old_slot))
        assert response.status_code == 400

    def test_student_not_in_course_cannot_check_in(self, client, live_lecture):
        _, session_id = live_lecture
        assert scan(client, session_id, email=OUTSIDER, name="Outsider").status_code == 403

    def test_session_end_locks_check_ins(self, client, live_lecture):
        _, session_id = live_lecture
        lock = client.post(f"/api/sessions/{session_id}/qr-control",
                           params={"lecturer_email": LECTURER, "enabled": False})
        assert lock.status_code == 200
        assert scan(client, session_id).status_code == 409
        status = client.get(f"/api/sessions/{session_id}/status").json()
        assert status["attendance_open"] is False

    def test_no_check_in_after_lecture_closed(self, client, live_lecture):
        _, session_id = live_lecture
        close_lecture(client, session_id)
        assert scan(client, session_id).status_code == 400


class TestAttendanceCrossCheckFlow:
    """Feature 1 – the main feature: photo count, cross-check, approval and Excel."""

    def test_more_checkins_than_people_needs_explicit_approval(self, client, live_lecture):
        _, session_id = live_lecture
        scan(client, session_id, STUDENT, "Yair Cohen")
        scan(client, session_id, STUDENT_2, "Student Two")
        result = set_people_count(client, session_id, 1)
        assert result["crosscheck"]["status"] == "more_checkins"
        refused = client.post(f"/api/sessions/{session_id}/attendance/approve", params={"lecturer_email": LECTURER})
        assert refused.status_code == 409
        approved = client.post(f"/api/sessions/{session_id}/attendance/approve",
                               params={"lecturer_email": LECTURER, "approve_mismatch": True})
        assert approved.status_code == 200
        assert approved.json()["excel_report_generated"] == f"attendance_session_{session_id}.xlsx"

    def test_more_people_than_checkins_is_approved(self, client, live_lecture):
        _, session_id = live_lecture
        scan(client, session_id)
        assert set_people_count(client, session_id, 30)["crosscheck"]["status"] == "more_people"
        approved = client.post(f"/api/sessions/{session_id}/attendance/approve", params={"lecturer_email": LECTURER})
        assert approved.status_code == 200

    def test_photo_count_locks_check_ins(self, client, live_lecture):
        _, session_id = live_lecture
        set_people_count(client, session_id, 10)
        assert scan(client, session_id).status_code == 409

    def test_restart_attendance_clears_check_ins_and_count(self, client, live_lecture):
        _, session_id = live_lecture
        scan(client, session_id)
        set_people_count(client, session_id, 0)
        reset = client.post(f"/api/sessions/{session_id}/reset-attendance", params={"lecturer_email": LECTURER})
        assert reset.status_code == 200
        state = client.get(f"/api/sessions/{session_id}/live-state", params={"lecturer_email": LECTURER}).json()
        assert state["checked_in_count"] == 0
        assert state["detected_people"] is None
        assert state["qr_enabled"] is True
        assert scan(client, session_id).status_code == 200  # a new attendance round works

    def test_invalid_people_count_is_rejected(self, client, live_lecture):
        _, session_id = live_lecture
        response = client.post(f"/api/sessions/{session_id}/photo/manual-count",
                               params={"lecturer_email": LECTURER, "people": -1})
        assert response.status_code == 400

    def test_photo_upload_needs_valid_token(self, client, live_lecture):
        _, session_id = live_lecture
        response = client.post(f"/api/sessions/{session_id}/photo", params={"token": "wrong"},
                               files={"file": ("class.jpg", b"not-a-photo", "image/jpeg")})
        assert response.status_code == 403

    def test_excel_report_has_no_id_numbers(self, client, live_lecture):
        _, session_id = live_lecture
        scan(client, session_id, STUDENT, "Yair Cohen")
        set_people_count(client, session_id, 5)
        client.post(f"/api/sessions/{session_id}/attendance/approve", params={"lecturer_email": LECTURER})
        report = client.get(f"/api/sessions/{session_id}/attendance-report", params={"lecturer_email": LECTURER})
        assert report.status_code == 200
        rows = list(openpyxl.load_workbook(io.BytesIO(report.content)).active.values)
        assert list(rows[0]) == ["Student Name", "Institutional Email", "Timestamp", "Status"]
        assert rows[1][0] == "Yair Cohen" and rows[1][1] == STUDENT and rows[1][3] == "Present"
        assert len(rows) == 2

    def test_only_lecturer_downloads_report(self, client, live_lecture):
        _, session_id = live_lecture
        set_people_count(client, session_id, 0)
        client.post(f"/api/sessions/{session_id}/attendance/approve", params={"lecturer_email": LECTURER})
        response = client.get(f"/api/sessions/{session_id}/attendance-report", params={"lecturer_email": STUDENT})
        assert response.status_code == 403


class TestForum:
    def post(self, client, session_id, email=STUDENT, message="What is polymorphism?"):
        return client.post("/api/forum/post", params={
            "session_id": session_id, "student_email": email, "student_name": "Yair Cohen", "message": message})

    def test_student_posts_question(self, client, live_lecture):
        _, session_id = live_lecture
        assert self.post(client, session_id).status_code == 200
        forum = client.get(f"/api/sessions/{session_id}/forum").json()
        assert forum[0]["message"] == "What is polymorphism?"

    def test_empty_question_is_rejected(self, client, live_lecture):
        _, session_id = live_lecture
        assert self.post(client, session_id, message="   ").status_code == 400

    def test_outsider_cannot_post(self, client, live_lecture):
        _, session_id = live_lecture
        assert self.post(client, session_id, email=OUTSIDER).status_code == 403

    def test_lecturer_and_students_reply_in_thread(self, client, live_lecture):
        _, session_id = live_lecture
        self.post(client, session_id)
        post_id = client.get(f"/api/sessions/{session_id}/forum").json()[0]["id"]
        for email, name in ((LECTURER, "Dr. Ohad"), (STUDENT_2, "Student Two")):
            reply = client.post(f"/api/forum/{post_id}/replies",
                                params={"email": email, "name": name, "message": "Good question"})
            assert reply.status_code == 200
        assert len(client.get(f"/api/sessions/{session_id}/forum").json()[0]["replies"]) == 2

    def test_forum_stays_open_after_lecture(self, client, live_lecture):
        _, session_id = live_lecture
        close_lecture(client, session_id)
        assert self.post(client, session_id, message="Question after class").status_code == 200


class TestPolls:
    def create(self, client, session_id, options='["A", "B", "C"]', **extra):
        return client.post("/api/polls/create", params={
            "session_id": session_id, "question": "Which is correct?", "options": options,
            "lecturer_email": LECTURER, **extra})

    def vote(self, client, poll_id, option, email=STUDENT):
        return client.post("/api/polls/vote", params={
            "poll_id": poll_id, "student_email": email, "selected_option": option})

    def results(self, client, session_id):
        return client.get(f"/api/sessions/{session_id}/polls").json()[0]

    def test_live_poll_vote_and_results(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id).json()["poll_id"]
        assert self.vote(client, poll_id, "A").status_code == 200
        assert self.vote(client, poll_id, "B", STUDENT_2).status_code == 200
        poll = self.results(client, session_id)
        assert poll["results"] == {"A": 1, "B": 1, "C": 0} and poll["total_votes"] == 2

    def test_student_can_change_single_answer_vote(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id).json()["poll_id"]
        self.vote(client, poll_id, "A")
        self.vote(client, poll_id, "C")
        assert self.results(client, session_id)["results"] == {"A": 0, "B": 0, "C": 1}

    def test_multiple_answer_poll_toggles_options(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id, allow_multiple=True).json()["poll_id"]
        self.vote(client, poll_id, "A")
        self.vote(client, poll_id, "B")
        self.vote(client, poll_id, "A")  # second tap removes A
        assert self.results(client, session_id)["results"] == {"A": 0, "B": 1, "C": 0}

    @pytest.mark.parametrize("options", ['["Only one"]', '["Same", "Same"]', "[]"])
    def test_invalid_options_are_rejected(self, client, live_lecture, options):
        _, session_id = live_lecture
        assert self.create(client, session_id, options=options).status_code == 400

    def test_invalid_choice_is_rejected(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id).json()["poll_id"]
        assert self.vote(client, poll_id, "Z").status_code == 400

    def test_outsider_cannot_vote(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id).json()["poll_id"]
        assert self.vote(client, poll_id, "A", OUTSIDER).status_code == 403

    def test_voting_locks_when_lecture_closes(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id).json()["poll_id"]
        close_lecture(client, session_id)
        assert self.vote(client, poll_id, "A").status_code == 400

    def test_post_lecture_poll_requires_time_limit(self, client, live_lecture):
        _, session_id = live_lecture
        close_lecture(client, session_id)
        assert self.create(client, session_id).status_code == 400
        poll_id = self.create(client, session_id, duration_minutes=30).json()["poll_id"]
        assert self.vote(client, poll_id, "B").status_code == 200
        assert self.results(client, session_id)["expires_at"] is not None

    def test_post_lecture_poll_closes_when_time_is_up(self, client, live_lecture):
        _, session_id = live_lecture
        close_lecture(client, session_id)
        poll_id = self.create(client, session_id, duration_minutes=1).json()["poll_id"]
        db = SessionLocal()
        try:
            window = db.query(main.PollTimeWindow).filter(main.PollTimeWindow.poll_id == poll_id).first()
            window.closes_at = main.datetime.utcnow() - main.timedelta(seconds=1)
            db.commit()
        finally:
            db.close()
        assert self.vote(client, poll_id, "A").status_code == 400

    def test_poll_discussion_thread(self, client, live_lecture):
        _, session_id = live_lecture
        poll_id = self.create(client, session_id).json()["poll_id"]
        comment = client.post(f"/api/polls/{poll_id}/comments",
                              params={"email": STUDENT, "name": "Yair Cohen", "message": "Why not C?"})
        assert comment.status_code == 200
        assert self.results(client, session_id)["comments"][0]["message"] == "Why not C?"


class TestLectureSummary:
    def test_summary_without_ai_key_is_refused_not_invented(self, client, live_lecture):
        _, session_id = live_lecture
        response = client.post(f"/api/sessions/{session_id}/summarize-video",
                               data={"lecturer_email": LECTURER, "video_url": "https://youtu.be/demo"})
        assert response.status_code == 503

    def test_student_cannot_request_summary(self, client, live_lecture):
        _, session_id = live_lecture
        response = client.post(f"/api/sessions/{session_id}/summarize-video",
                               data={"lecturer_email": STUDENT, "video_url": "https://youtu.be/demo"})
        assert response.status_code == 403

    def test_students_read_saved_summary(self, client, live_lecture):
        _, session_id = live_lecture
        client.post(f"/api/sessions/{session_id}/ai-summary", params={"summary_text": "Today: inheritance."})
        assert client.get(f"/api/sessions/{session_id}/ai-summary").json()["ai_summary"] == "Today: inheritance."

    def test_no_summary_yet(self, client, live_lecture):
        _, session_id = live_lecture
        assert client.get(f"/api/sessions/{session_id}/ai-summary").json()["ai_summary"] == "No summary available yet."


class TestAssignments:
    @pytest.fixture
    def assignment(self, client, live_lecture):
        course_id, _ = live_lecture
        response = client.post("/api/assignments/create", params={
            "course_id": course_id, "title": "Ex1", "description": "Implement a Stack class",
            "due_date": "2026-12-31", "lecturer_email": LECTURER})
        assert response.status_code == 200, response.text
        return response.json()["assignment_id"]

    def submit(self, client, assignment_id, email=STUDENT, content=b"class Stack:\n    pass\n"):
        return client.post(f"/api/assignments/{assignment_id}/submit-file", data={"student_email": email},
                           files={"file": ("stack.py", content, "text/x-python")})

    def test_invalid_due_date_is_rejected(self, client, live_lecture):
        course_id, _ = live_lecture
        response = client.post("/api/assignments/create", params={
            "course_id": course_id, "title": "Ex1", "description": "x",
            "due_date": "31/12/2026", "lecturer_email": LECTURER})
        assert response.status_code == 400

    def test_student_cannot_create_assignment(self, client, live_lecture):
        course_id, _ = live_lecture
        response = client.post("/api/assignments/create", params={
            "course_id": course_id, "title": "Ex1", "description": "x",
            "due_date": "2026-12-31", "lecturer_email": STUDENT})
        assert response.status_code == 403

    def test_submission_without_ai_key_gets_no_invented_grade(self, client, assignment):
        response = self.submit(client, assignment)
        assert response.status_code == 200
        data = response.json()
        assert data["ai_status"] == "pending_configuration"
        assert data.get("llm_grade") is None and data["final_grade_approved"] is False

    def test_unsupported_file_type_is_rejected(self, client, assignment):
        response = client.post(f"/api/assignments/{assignment}/submit-file", data={"student_email": STUDENT},
                               files={"file": ("virus.exe", b"MZ", "application/octet-stream")})
        assert response.status_code == 415

    def test_lecturer_cannot_submit_as_student(self, client, assignment):
        assert self.submit(client, assignment, email=LECTURER).status_code == 403

    def test_outsider_cannot_submit(self, client, assignment):
        assert self.submit(client, assignment, email=OUTSIDER).status_code == 403

    def test_resubmission_replaces_previous(self, client, assignment):
        self.submit(client, assignment)
        self.submit(client, assignment, content=b"class Stack:\n    def push(self, x): ...\n")
        subs = client.get(f"/api/assignments/{assignment}/submissions", params={"lecturer_email": LECTURER}).json()
        assert len(subs) == 1

    def test_lecturer_approves_final_grade(self, client, assignment):
        submission_id = self.submit(client, assignment).json()["submission_id"]
        approve = client.post(f"/api/assignments/submission/{submission_id}/grade",
                              params={"grade": "92", "approved": True, "lecturer_email": LECTURER})
        assert approve.status_code == 200
        mine = client.get(f"/api/assignments/{assignment}/my-submission", params={"student_email": STUDENT}).json()
        assert mine["llm_grade"] == "92" and mine["final_grade_approved"] is True

    @pytest.mark.parametrize("grade", ["101", "-5", "A+"])
    def test_invalid_grade_is_rejected(self, client, assignment, grade):
        submission_id = self.submit(client, assignment).json()["submission_id"]
        response = client.post(f"/api/assignments/submission/{submission_id}/grade",
                               params={"grade": grade, "approved": True, "lecturer_email": LECTURER})
        assert response.status_code == 400

    def test_student_cannot_approve_grade(self, client, assignment):
        submission_id = self.submit(client, assignment).json()["submission_id"]
        response = client.post(f"/api/assignments/submission/{submission_id}/grade",
                               params={"grade": "100", "approved": True, "lecturer_email": STUDENT})
        assert response.status_code == 403

    def test_students_cannot_see_others_submissions(self, client, assignment):
        other_id = self.submit(client, assignment, email=STUDENT_2).json()["submission_id"]
        file_response = client.get(f"/api/assignments/submission/{other_id}/file", params={"email": STUDENT})
        assert file_response.status_code == 403
        listing = client.get(f"/api/assignments/{assignment}/submissions", params={"lecturer_email": STUDENT})
        assert listing.status_code == 403

    def test_feedback_forum_has_no_grades_or_names(self, client, assignment):
        submission_id = self.submit(client, assignment).json()["submission_id"]
        # Simulate a finished AI review (Gemini is not available in tests).
        db = SessionLocal()
        try:
            sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
            sub.llm_grade = "88"
            sub.llm_review = '{"score": 88, "review": "Clear code, add tests."}'
            meta = db.query(main.SubmissionDocument).filter(main.SubmissionDocument.submission_id == submission_id).first()
            meta.ai_status = "reviewed"
            db.commit()
        finally:
            db.close()
        # Before the lecturer approves, students see nothing of it.
        assert client.get(f"/api/assignments/{assignment}/feedback-forum", params={"email": STUDENT_2}).json() == []
        client.post(f"/api/assignments/submission/{submission_id}/grade",
                    params={"grade": "88", "approved": True, "lecturer_email": LECTURER})
        forum = client.get(f"/api/assignments/{assignment}/feedback-forum", params={"email": STUDENT_2})
        assert forum.status_code == 200
        assert forum.json() == [{"label": "Submission 1", "review": "Clear code, add tests."}]

    def test_student_sees_grade_only_after_lecturer_approves(self, client, assignment):
        submission_id = self.submit(client, assignment).json()["submission_id"]
        db = SessionLocal()
        try:  # simulate a finished AI review
            sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
            sub.llm_grade, sub.llm_review = "77", '{"score": 77, "review": "Good."}'
            db.query(main.SubmissionDocument).filter(
                main.SubmissionDocument.submission_id == submission_id).first().ai_status = "reviewed"
            db.commit()
        finally:
            db.close()
        mine = client.get(f"/api/assignments/{assignment}/my-submission", params={"student_email": STUDENT}).json()
        assert mine["llm_grade"] is None and mine["llm_review"] is None and mine["final_grade_approved"] is False
        lecturer_view = client.get(f"/api/assignments/{assignment}/submissions", params={"lecturer_email": LECTURER}).json()
        assert lecturer_view[0]["llm_grade"] == "77"
        client.post(f"/api/assignments/submission/{submission_id}/grade",
                    params={"grade": "80", "approved": True, "lecturer_email": LECTURER})
        mine = client.get(f"/api/assignments/{assignment}/my-submission", params={"student_email": STUDENT}).json()
        assert mine["llm_grade"] == "80" and mine["final_grade_approved"] is True

    def test_unreviewed_submissions_are_not_in_feedback_forum(self, client, assignment):
        self.submit(client, assignment)
        assert client.get(f"/api/assignments/{assignment}/feedback-forum", params={"email": STUDENT}).json() == []

    def test_comparison_is_lecturer_only(self, client, assignment):
        self.submit(client, assignment)
        self.submit(client, assignment, email=STUDENT_2)
        assert client.get(f"/api/assignments/{assignment}/comparison",
                          params={"lecturer_email": STUDENT}).status_code == 403
        report = client.get(f"/api/assignments/{assignment}/comparison", params={"lecturer_email": LECTURER})
        assert report.status_code == 200
        assert report.json()["total_submissions"] == 2
        assert len(report.json()["text_overlap_pairs"]) == 1

    def test_ai_comparison_needs_two_submissions(self, client, assignment):
        self.submit(client, assignment)
        response = client.post(f"/api/assignments/{assignment}/run-comparison", params={"lecturer_email": LECTURER})
        assert response.status_code == 400
