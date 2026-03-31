from models import db


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    roll_number = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    guardian = db.Column(db.String(100))
    photo = db.Column(db.String(255))

    marks = db.relationship('Mark', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.user.name if self.user else self.id}>'
