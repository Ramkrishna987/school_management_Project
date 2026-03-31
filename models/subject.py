from models import db


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False, unique=True)

    assignments = db.relationship('TeacherAssignment', backref='subject', lazy='dynamic')

    def __repr__(self):
        return f'<Subject {self.subject_name}>'
