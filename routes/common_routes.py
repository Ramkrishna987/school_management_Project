from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import User
from models.teacher import Teacher
from models.student import Student
from models.class_model import Class
from models.subject import Subject
from models.assignment import TeacherAssignment
from models.marks import Mark
from models import db

common_bp = Blueprint('common', __name__)


@common_bp.route('/')
def index():
    try:
        teachers = Teacher.query.join(User).limit(6).all()
    except Exception:
        teachers = []
    return render_template('common/index.html', teachers=teachers)


@common_bp.route('/about')
def about():
    return render_template('common/about.html')


@common_bp.route('/faculty')
def faculty():
    try:
        teachers = Teacher.query.join(User).all()
    except Exception:
        teachers = []
    return render_template('common/faculty.html', teachers=teachers)


@common_bp.route('/contact')
def contact():
    return render_template('common/contact.html')


@common_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        role = current_user.role
        data = {}

        if role == 'admin':
            try:
                data['total_students'] = Student.query.count()
                data['total_teachers'] = Teacher.query.count()
                data['total_classes'] = Class.query.count()
                data['total_subjects'] = Subject.query.count()
                data['total_assignments'] = TeacherAssignment.query.count()
                data['recent_teachers'] = Teacher.query.join(User).order_by(Teacher.id.desc()).limit(5).all()
                data['recent_students'] = Student.query.join(User).order_by(Student.id.desc()).limit(5).all()
            except Exception:
                data.setdefault('total_students', 0)
                data.setdefault('total_teachers', 0)
                data.setdefault('total_classes', 0)
                data.setdefault('total_subjects', 0)
                data.setdefault('total_assignments', 0)
                data.setdefault('recent_teachers', [])
                data.setdefault('recent_students', [])

        elif role == 'teacher':
            try:
                teacher = current_user.teacher
                if not teacher:
                    # Render error — do NOT redirect to logout/login (causes redirect loop)
                    return render_template('common/error.html',
                                           code=403,
                                           message='Profile Not Found',
                                           detail='Teacher profile not found. Please contact your administrator.'), 403
                assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
                data['assignments'] = assignments
                data['total_assignments'] = len(assignments)
                class_ids = list(set(a.class_id for a in assignments))
                data['total_students'] = Student.query.filter(
                    Student.class_id.in_(class_ids)).count() if class_ids else 0
                data['total_marks_entered'] = Mark.query.filter_by(teacher_id=teacher.id).count()
            except Exception:
                data.setdefault('assignments', [])
                data.setdefault('total_assignments', 0)
                data.setdefault('total_students', 0)
                data.setdefault('total_marks_entered', 0)

        elif role == 'student':
            try:
                student = current_user.student
                if not student:
                    # Render error — do NOT redirect to logout/login (causes redirect loop)
                    return render_template('common/error.html',
                                           code=403,
                                           message='Profile Not Found',
                                           detail='Student profile not found. Please contact your administrator.'), 403
                marks_list = Mark.query.filter_by(student_id=student.id).all()
                data['marks'] = marks_list
                total = sum(m.marks for m in marks_list)
                max_total = sum(m.max_marks for m in marks_list)
                data['percentage'] = round((total / max_total * 100), 2) if max_total else 0
                data['student'] = student
            except Exception:
                data.setdefault('marks', [])
                data.setdefault('percentage', 0)
                data.setdefault('student', None)

        return render_template('common/dashboard.html', data=data, role=role)

    except Exception:
        # IMPORTANT: Never redirect to login here — causes ERR_TOO_MANY_REDIRECTS
        # because @login_required will redirect unauthenticated users back to login.
        return render_template('common/error.html',
                               code=500,
                               message='Dashboard Error',
                               detail='Could not load the dashboard. '
                                      'Please check your database connection and try again.'), 500
