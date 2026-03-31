from app import app, db
from models.user import User
from models.teacher import Teacher
from models.student import Student
from models.class_model import Class
from models.subject import Subject
from models.assignment import TeacherAssignment


def seed():
    with app.app_context():
        db.create_all()

        # Admin
        if not User.query.filter_by(email='admin@school.com').first():
            admin = User(name='Admin', email='admin@school.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin created: admin@school.com / admin123')

        # Classes
        class_data = [
            ('Class 10', 'A'), ('Class 10', 'B'),
            ('Class 11', 'A'), ('Class 12', 'A')
        ]
        classes = {}
        for cname, section in class_data:
            key = f'{cname}-{section}'
            existing = Class.query.filter_by(class_name=cname, section=section).first()
            if not existing:
                c = Class(class_name=cname, section=section)
                db.session.add(c)
                db.session.flush()
                classes[key] = c
            else:
                classes[key] = existing
        db.session.commit()
        print('✅ Classes created')

        # Subjects
        subject_names = ['Mathematics', 'Physics', 'Chemistry', 'English', 'Computer Science']
        subjects = {}
        for sname in subject_names:
            existing = Subject.query.filter_by(subject_name=sname).first()
            if not existing:
                s = Subject(subject_name=sname)
                db.session.add(s)
                db.session.flush()
                subjects[sname] = s
            else:
                subjects[sname] = existing
        db.session.commit()
        print('✅ Subjects created')

        # Sample Teacher
        if not User.query.filter_by(email='teacher@school.com').first():
            tu = User(name='Dr. Ravi Kumar', email='teacher@school.com', role='teacher')
            tu.set_password('teacher123')
            db.session.add(tu)
            db.session.flush()
            t = Teacher(user_id=tu.id, phone='9876543210',
                        qualification='M.Sc Mathematics', experience='10 years')
            db.session.add(t)
            db.session.flush()
            # Assign to Class 10-A, Mathematics
            cls = Class.query.filter_by(class_name='Class 10', section='A').first()
            sub = Subject.query.filter_by(subject_name='Mathematics').first()
            if cls and sub:
                a = TeacherAssignment(teacher_id=t.id, class_id=cls.id, subject_id=sub.id)
                db.session.add(a)
            db.session.commit()
            print('✅ Sample teacher: teacher@school.com / teacher123')

        # Sample Student
        if not User.query.filter_by(email='student@school.com').first():
            su = User(name='Arjun Reddy', email='student@school.com', role='student')
            su.set_password('student123')
            db.session.add(su)
            db.session.flush()
            cls = Class.query.filter_by(class_name='Class 10', section='A').first()
            s = Student(user_id=su.id, class_id=cls.id if cls else None,
                        roll_number='10A001', gender='Male',
                        phone='9000000001', guardian='Mr. Reddy')
            db.session.add(s)
            db.session.commit()
            print('✅ Sample student: student@school.com / student123')

        print('\n🎉 Seed complete!')
        print('─' * 40)
        print('Admin    → admin@school.com    / admin123')
        print('Teacher  → teacher@school.com  / teacher123')
        print('Student  → student@school.com  / student123')


if __name__ == '__main__':
    seed()
