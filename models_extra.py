"""
models_extra.py - extra tables for the Student Management app.

Adds: Course (teacher courses), Enrollment, Attendance, Result (CGPA),
Lab / LabRecord, Book / BookIssue (library).

Assumes your existing model is named User (table "user") with an `id`
column and a `role` column ("student" / "teacher").
"""
from datetime import date, timedelta


def create_models(db):
    class Course(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        code = db.Column(db.String(20), unique=True, nullable=False)
        name = db.Column(db.String(100), nullable=False)
        credits = db.Column(db.Integer, default=3)
        teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    class Enrollment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
        __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)

    class Attendance(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
        date = db.Column(db.Date, default=date.today, nullable=False)
        present = db.Column(db.Boolean, default=True, nullable=False)
        __table_args__ = (db.UniqueConstraint("student_id", "course_id", "date"),)

    class Result(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
        semester = db.Column(db.Integer, default=1)
        marks = db.Column(db.Float, nullable=False)  # out of 100

        @property
        def grade_point(self):
            m = self.marks
            if m >= 90: return 10
            if m >= 80: return 9
            if m >= 70: return 8
            if m >= 60: return 7
            if m >= 50: return 6
            if m >= 40: return 5
            return 0

    class Lab(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
        room = db.Column(db.String(50))

    class LabRecord(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        lab_id = db.Column(db.Integer, db.ForeignKey("lab.id"), nullable=False)
        experiment = db.Column(db.String(150))
        marks = db.Column(db.Float)  # out of 25 or 50, your choice
        date = db.Column(db.Date, default=date.today)

    class Book(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(150), nullable=False)
        author = db.Column(db.String(100))
        total_copies = db.Column(db.Integer, default=1)

        @property
        def available(self):
            issued = BookIssue.query.filter_by(book_id=self.id, return_date=None).count()
            return self.total_copies - issued

    class BookIssue(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
        issue_date = db.Column(db.Date, default=date.today)
        due_date = db.Column(db.Date, default=lambda: date.today() + timedelta(days=14))
        return_date = db.Column(db.Date, nullable=True)

        @property
        def fine(self):
            """Rs. 2 per day late."""
            end = self.return_date or date.today()
            late = (end - self.due_date).days
            return max(0, late) * 2

    # ---------- helper functions ----------
    def attendance_percentage(student_id, course_id=None):
        q = Attendance.query.filter_by(student_id=student_id)
        if course_id:
            q = q.filter_by(course_id=course_id)
        total = q.count()
        if total == 0:
            return 0.0
        present = q.filter_by(present=True).count()
        return round(present * 100 / total, 2)

    def cgpa(student_id):
        results = Result.query.filter_by(student_id=student_id).all()
        total_credits = 0
        points = 0
        for r in results:
            credits = Course.query.get(r.course_id).credits
            total_credits += credits
            points += r.grade_point * credits
        return round(points / total_credits, 2) if total_credits else 0.0

    return {
        "Course": Course, "Enrollment": Enrollment, "Attendance": Attendance,
        "Result": Result, "Lab": Lab, "LabRecord": LabRecord,
        "Book": Book, "BookIssue": BookIssue,
        "attendance_percentage": attendance_percentage, "cgpa": cgpa,
    }
