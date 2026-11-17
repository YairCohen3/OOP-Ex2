from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String)  # "lecturer" or "student"

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, unique=True, index=True)  # Unique auto-generated ID (e.g., CRS-482)
    title = Column(String)
    description = Column(Text)
    lecturer_email = Column(String)

    sessions = relationship("Session", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    students = relationship("StudentCourse", back_populates="course", cascade="all, delete-orphan")

class StudentCourse(Base):
    __tablename__ = "student_courses"
    id = Column(Integer, primary_key=True, index=True)
    student_email = Column(String)
    course_id = Column(String, ForeignKey("courses.course_id"))

    course = relationship("Course", back_populates="students")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"))
    is_active = Column(Boolean, default=True)  # True = Active session (green), False = Past session (grey)
    current_qr_code = Column(String, nullable=True)
    ai_summary = Column(Text, nullable=True)  # AI summary of the recorded class

    course = relationship("Course", back_populates="sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")
    polls = relationship("Poll", back_populates="session", cascade="all, delete-orphan")
    forum_posts = relationship("ForumPost", back_populates="session", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    student_email = Column(String)
    student_name = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("Session", back_populates="attendance_records")

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    question = Column(String)
    options = Column(Text)  # Comma-separated options
    is_active = Column(Boolean, default=True)

    session = relationship("Session", back_populates="polls")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")

class PollVote(Base):
    __tablename__ = "poll_votes"
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    student_email = Column(String)
    selected_option = Column(String)

    poll = relationship("Poll", back_populates="votes")

class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    student_email = Column(String)
    student_name = Column(String)
    message = Column(Text)
    reply = Column(Text, nullable=True)  # Lecturer or peer reply

    session = relationship("Session", back_populates="forum_posts")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"))
    title = Column(String)
    description = Column(Text)
    due_date = Column(String)  # Due date set by lecturer

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_email = Column(String)
    file_url = Column(String)
    llm_review = Column(Text, nullable=True)  # Deep review for class feedback forum (no grades)
    llm_grade = Column(String, nullable=True)  # Recommended grade from AI
    final_grade_approved = Column(Boolean, default=False)  # Confirmed by lecturer

    assignment = relationship("Assignment", back_populates="submissions")