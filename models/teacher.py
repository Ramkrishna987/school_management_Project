from models import db


class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(100))
    experience = db.Column(db.String(50))
    photo = db.Column(db.String(255))

    assignments = db.relationship('TeacherAssignment', backref='teacher', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Teacher {self.user.name if self.user else self.id}>'
