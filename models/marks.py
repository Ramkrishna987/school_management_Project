from models import db


class Mark(db.Model):
    __tablename__ = 'marks'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('teacher_assignments.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False, default=0)
    max_marks = db.Column(db.Float, nullable=False, default=100)
    exam_type = db.Column(db.String(50), default='Unit Test')

    subject = db.relationship('Subject')
    class_ = db.relationship('Class')
    teacher = db.relationship('Teacher')

    def grade(self):
        pct = (self.marks / self.max_marks * 100) if self.max_marks else 0
        if pct >= 90: return 'A+'
        if pct >= 80: return 'A'
        if pct >= 70: return 'B+'
        if pct >= 60: return 'B'
        if pct >= 50: return 'C'
        if pct >= 40: return 'D'
        return 'F'

    def percentage(self):
        return round((self.marks / self.max_marks * 100), 2) if self.max_marks else 0
