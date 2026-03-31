from models import db


class TeacherAssignment(db.Model):
    __tablename__ = 'teacher_assignments'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)

    marks = db.relationship('Mark', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Assignment T:{self.teacher_id} C:{self.class_id} S:{self.subject_id}>'
