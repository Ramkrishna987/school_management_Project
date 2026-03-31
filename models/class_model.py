from models import db


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))

    students = db.relationship('Student', backref='class_', lazy='dynamic')
    assignments = db.relationship('TeacherAssignment', backref='class_', lazy='dynamic')

    def __repr__(self):
        return f'<Class {self.class_name}-{self.section}>'
