import os, random, string
from flask import Blueprint, render_template, request, jsonify, current_app, url_for
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.user import User
from models.teacher import Teacher
from models.student import Student
from models.class_model import Class
from models.subject import Subject
from models.assignment import TeacherAssignment
from models.marks import Mark
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def save_photo(file_obj, prefix='photo'):
    if file_obj and allowed_file(file_obj.filename):
        filename = secure_filename(f"{prefix}_{file_obj.filename}")
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        path = os.path.join(upload_folder, filename)
        file_obj.save(path)
        return filename
    return None


def send_credentials(email, name, plain_password):
    try:
        from flask_mail import Message
        from app import mail
        msg = Message(
            subject='Your School Login Credentials',
            recipients=[email],
            body=f"""Hello {name},

Your account has been created.

Email: {email}
Password: {plain_password}

Please login and change your password after first login.

Regards,
School Admin"""
        )
        mail.send(msg)
    except Exception:
        pass  # Mail optional — credentials returned in response


def send_password_changed_mail(email, name, new_password):
    try:
        from flask_mail import Message
        from app import mail
        msg = Message(
            subject='Your School Password Has Been Changed',
            recipients=[email],
            body=f"""Hello {name},

Your password has been updated.

Email: {email}
New Password: {new_password}

If you did not request this change, please contact the school admin immediately.

Regards,
School Admin"""
        )
        mail.send(msg)
    except Exception:
        pass


# ─── PAGES ───────────────────────────────────────────────────────────────────

@admin_bp.route('/teachers')
@login_required
@admin_required
def teachers_page():
    classes = Class.query.order_by(Class.class_name).all()
    subjects = Subject.query.order_by(Subject.subject_name).all()
    return render_template('admin/teachers.html', classes=classes, subjects=subjects)


@admin_bp.route('/students')
@login_required
@admin_required
def students_page():
    classes = Class.query.order_by(Class.class_name).all()
    return render_template('admin/students.html', classes=classes)


@admin_bp.route('/classes')
@login_required
@admin_required
def classes_page():
    return render_template('admin/classes.html')


@admin_bp.route('/assignments')
@login_required
@admin_required
def assignments_page():
    teachers = Teacher.query.join(User).all()
    classes = Class.query.order_by(Class.class_name).all()
    subjects = Subject.query.order_by(Subject.subject_name).all()
    return render_template('admin/assignments.html',
                           teachers=teachers, classes=classes, subjects=subjects)


# ─── TEACHER CRUD APIs ───────────────────────────────────────────────────────

@admin_bp.route('/api/teachers', methods=['GET'])
@login_required
@admin_required
def api_teachers_list():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        q = Teacher.query.join(User)
        if search:
            q = q.filter(User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%'))
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
        teachers = []
        for t in pagination.items:
            teachers.append({
                'id': t.id, 'user_id': t.user_id,
                'name': t.user.name, 'email': t.user.email,
                'phone': t.phone, 'qualification': t.qualification,
                'experience': t.experience,
                'photo': t.photo or ''
            })
        return jsonify({'teachers': teachers, 'total': pagination.total,
                        'pages': pagination.pages, 'page': page})
    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to load teachers. Please try again.'}), 500


@admin_bp.route('/api/teachers', methods=['POST'])
@login_required
@admin_required
def api_teacher_create():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        qualification = request.form.get('qualification', '').strip()
        experience = request.form.get('experience', '').strip()

        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        if '@' not in email:
            return jsonify({'error': 'Invalid email address format'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        plain_pw = generate_password()
        user = User(name=name, email=email, role='teacher')
        user.set_password(plain_pw)
        db.session.add(user)
        db.session.flush()

        photo_file = request.files.get('photo')
        photo = save_photo(photo_file, prefix=f'teacher_{user.id}')

        teacher = Teacher(user_id=user.id, phone=phone,
                          qualification=qualification, experience=experience, photo=photo)
        db.session.add(teacher)
        db.session.commit()
        send_credentials(email, name, plain_pw)

        return jsonify({'message': f'Teacher created. Password: {plain_pw}', 'plain_password': plain_pw}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create teacher. Please check your input and try again.'}), 500


@admin_bp.route('/api/teachers/<int:tid>', methods=['GET'])
@login_required
@admin_required
def api_teacher_get(tid):
    try:
        t = Teacher.query.get_or_404(tid)
        return jsonify({
            'id': t.id, 'user_id': t.user_id,
            'name': t.user.name, 'email': t.user.email,
            'phone': t.phone or '', 'qualification': t.qualification or '',
            'experience': t.experience or '', 'photo': t.photo or ''
        })
    except Exception as e:
        return jsonify({'error': 'Teacher not found or could not be loaded.'}), 404


@admin_bp.route('/api/teachers/<int:tid>', methods=['PUT'])
@login_required
@admin_required
def api_teacher_update(tid):
    try:
        t = Teacher.query.get_or_404(tid)
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        if not name or not email:
            return jsonify({'error': 'Name and email required'}), 400
        if '@' not in email:
            return jsonify({'error': 'Invalid email address format'}), 400
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != t.user_id:
            return jsonify({'error': 'Email already in use'}), 400

        t.user.name = name
        t.user.email = email
        t.phone = request.form.get('phone', '').strip()
        t.qualification = request.form.get('qualification', '').strip()
        t.experience = request.form.get('experience', '').strip()

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            t.photo = save_photo(photo_file, prefix=f'teacher_{t.id}')

        db.session.commit()
        return jsonify({'message': 'Teacher updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update teacher. Please try again.'}), 500


@admin_bp.route('/api/teachers/<int:tid>', methods=['DELETE'])
@login_required
@admin_required
def api_teacher_delete(tid):
    try:
        t = Teacher.query.get_or_404(tid)
        user = t.user
        db.session.delete(t)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Teacher deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete teacher. They may have associated records.'}), 500


# ─── STUDENT CRUD APIs ───────────────────────────────────────────────────────

@admin_bp.route('/api/students', methods=['GET'])
@login_required
@admin_required
def api_students_list():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        q = Student.query.join(User)
        if search:
            q = q.filter(User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%'))
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
        students = []
        for s in pagination.items:
            students.append({
                'id': s.id, 'user_id': s.user_id,
                'name': s.user.name, 'email': s.user.email,
                'class_id': s.class_id,
                'class_name': f"{s.class_.class_name}-{s.class_.section}" if s.class_ else '',
                'roll_number': s.roll_number or '',
                'gender': s.gender or '',
                'dob': str(s.dob) if s.dob else '',
                'phone': s.phone or '', 'address': s.address or '',
                'guardian': s.guardian or '', 'photo': s.photo or ''
            })
        return jsonify({'students': students, 'total': pagination.total,
                        'pages': pagination.pages, 'page': page})
    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to load students. Please try again.'}), 500


@admin_bp.route('/api/students', methods=['POST'])
@login_required
@admin_required
def api_student_create():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        class_id = request.form.get('class_id')
        roll_number = request.form.get('roll_number', '').strip()
        gender = request.form.get('gender', '').strip()
        dob = request.form.get('dob') or None
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        guardian = request.form.get('guardian', '').strip()

        if not name or not email:
            return jsonify({'error': 'Name and email required'}), 400
        if '@' not in email:
            return jsonify({'error': 'Invalid email address format'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        plain_pw = generate_password()
        user = User(name=name, email=email, role='student')
        user.set_password(plain_pw)
        db.session.add(user)
        db.session.flush()

        photo_file = request.files.get('photo')
        photo = save_photo(photo_file, prefix=f'student_{user.id}')

        from datetime import date
        dob_val = None
        if dob:
            try:
                from datetime import datetime
                dob_val = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

        student = Student(user_id=user.id, class_id=class_id or None,
                          roll_number=roll_number, gender=gender, dob=dob_val,
                          phone=phone, address=address, guardian=guardian, photo=photo)
        db.session.add(student)
        db.session.commit()
        send_credentials(email, name, plain_pw)
        return jsonify({'message': f'Student created. Password: {plain_pw}', 'plain_password': plain_pw}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create student. Please check your input and try again.'}), 500


@admin_bp.route('/api/students/<int:sid>', methods=['GET'])
@login_required
@admin_required
def api_student_get(sid):
    try:
        s = Student.query.get_or_404(sid)
        return jsonify({
            'id': s.id, 'name': s.user.name, 'email': s.user.email,
            'class_id': s.class_id or '', 'roll_number': s.roll_number or '',
            'gender': s.gender or '', 'dob': str(s.dob) if s.dob else '',
            'phone': s.phone or '', 'address': s.address or '',
            'guardian': s.guardian or '', 'photo': s.photo or ''
        })
    except Exception as e:
        return jsonify({'error': 'Student not found or could not be loaded.'}), 404


@admin_bp.route('/api/students/<int:sid>', methods=['PUT'])
@login_required
@admin_required
def api_student_update(sid):
    try:
        s = Student.query.get_or_404(sid)
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        if not name or not email:
            return jsonify({'error': 'Name and email required'}), 400
        if '@' not in email:
            return jsonify({'error': 'Invalid email address format'}), 400
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != s.user_id:
            return jsonify({'error': 'Email already in use'}), 400

        s.user.name = name
        s.user.email = email
        s.class_id = request.form.get('class_id') or None
        s.roll_number = request.form.get('roll_number', '').strip()
        s.gender = request.form.get('gender', '').strip()
        dob = request.form.get('dob')
        if dob:
            try:
                from datetime import datetime
                s.dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        s.phone = request.form.get('phone', '').strip()
        s.address = request.form.get('address', '').strip()
        s.guardian = request.form.get('guardian', '').strip()

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            s.photo = save_photo(photo_file, prefix=f'student_{s.id}')

        db.session.commit()
        return jsonify({'message': 'Student updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update student. Please try again.'}), 500


@admin_bp.route('/api/students/<int:sid>', methods=['DELETE'])
@login_required
@admin_required
def api_student_delete(sid):
    try:
        s = Student.query.get_or_404(sid)
        user = s.user
        db.session.delete(s)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Student deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete student. They may have associated records.'}), 500


# ─── CLASS & SUBJECT APIs ────────────────────────────────────────────────────

@admin_bp.route('/api/classes', methods=['GET'])
@login_required
@admin_required
def api_classes_list():
    try:
        classes = Class.query.order_by(Class.class_name, Class.section).all()
        return jsonify({'classes': [{'id': c.id, 'class_name': c.class_name,
                                      'section': c.section,
                                      'student_count': c.students.count()} for c in classes]})
    except Exception as e:
        return jsonify({'error': 'Failed to load classes. Please try again.'}), 500


@admin_bp.route('/api/classes', methods=['POST'])
@login_required
@admin_required
def api_class_create():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        name = (data.get('class_name') or '').strip()
        section = (data.get('section') or '').strip()
        if not name:
            return jsonify({'error': 'Class name is required'}), 400
        # Duplicate check
        existing = Class.query.filter_by(class_name=name, section=section).first()
        if existing:
            return jsonify({'error': f'Class "{name}-{section or "No Section"}" already exists'}), 400
        c = Class(class_name=name, section=section)
        db.session.add(c)
        db.session.commit()
        return jsonify({'message': 'Class created successfully', 'id': c.id,
                        'class_name': c.class_name, 'section': c.section}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create class. Please try again.'}), 500


@admin_bp.route('/api/classes/<int:cid>', methods=['DELETE'])
@login_required
@admin_required
def api_class_delete(cid):
    try:
        c = Class.query.get_or_404(cid)
        db.session.delete(c)
        db.session.commit()
        return jsonify({'message': 'Class deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete class. It may have students assigned to it.'}), 500


@admin_bp.route('/api/subjects', methods=['GET'])
@login_required
@admin_required
def api_subjects_list():
    try:
        subjects = Subject.query.order_by(Subject.subject_name).all()
        return jsonify({'subjects': [{'id': s.id, 'subject_name': s.subject_name} for s in subjects]})
    except Exception as e:
        return jsonify({'error': 'Failed to load subjects. Please try again.'}), 500


@admin_bp.route('/api/subjects', methods=['POST'])
@login_required
@admin_required
def api_subject_create():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        name = (data.get('subject_name') or '').strip()
        if not name:
            return jsonify({'error': 'Subject name is required'}), 400
        if Subject.query.filter_by(subject_name=name).first():
            return jsonify({'error': f'Subject "{name}" already exists'}), 400
        s = Subject(subject_name=name)
        db.session.add(s)
        db.session.commit()
        return jsonify({'message': 'Subject created successfully', 'id': s.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create subject. Please try again.'}), 500


@admin_bp.route('/api/subjects/<int:sid>', methods=['DELETE'])
@login_required
@admin_required
def api_subject_delete(sid):
    try:
        s = Subject.query.get_or_404(sid)
        db.session.delete(s)
        db.session.commit()
        return jsonify({'message': 'Subject deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete subject. It may be in use by assignments.'}), 500


# ─── ASSIGNMENT APIs ─────────────────────────────────────────────────────────

@admin_bp.route('/api/assignments', methods=['GET'])
@login_required
@admin_required
def api_assignments_list():
    try:
        assignments = TeacherAssignment.query.all()
        result = []
        for a in assignments:
            result.append({
                'id': a.id,
                'teacher_id': a.teacher_id,
                'teacher_name': a.teacher.user.name,
                'class_id': a.class_id,
                'class_name': f"{a.class_.class_name}-{a.class_.section}",
                'subject_id': a.subject_id,
                'subject_name': a.subject.subject_name
            })
        return jsonify({'assignments': result})
    except Exception as e:
        return jsonify({'error': 'Failed to load assignments. Please try again.'}), 500


@admin_bp.route('/api/assignments', methods=['POST'])
@login_required
@admin_required
def api_assignment_create():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        teacher_id = data.get('teacher_id')
        class_id = data.get('class_id')
        subject_id = data.get('subject_id')
        if not all([teacher_id, class_id, subject_id]):
            return jsonify({'error': 'All fields (Teacher, Class, Subject) are required'}), 400
        # Validate referenced records exist
        if not Teacher.query.get(teacher_id):
            return jsonify({'error': 'Selected teacher does not exist'}), 400
        if not Class.query.get(class_id):
            return jsonify({'error': 'Selected class does not exist'}), 400
        if not Subject.query.get(subject_id):
            return jsonify({'error': 'Selected subject does not exist'}), 400
        existing = TeacherAssignment.query.filter_by(
            teacher_id=teacher_id, class_id=class_id, subject_id=subject_id).first()
        if existing:
            return jsonify({'error': 'This exact assignment (Teacher + Class + Subject) already exists'}), 400
        a = TeacherAssignment(teacher_id=teacher_id, class_id=class_id, subject_id=subject_id)
        db.session.add(a)
        db.session.commit()
        return jsonify({'message': 'Assignment created successfully', 'id': a.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create assignment. Please try again.'}), 500


@admin_bp.route('/api/assignments/<int:aid>', methods=['DELETE'])
@login_required
@admin_required
def api_assignment_delete(aid):
    try:
        a = TeacherAssignment.query.get_or_404(aid)
        db.session.delete(a)
        db.session.commit()
        return jsonify({'message': 'Assignment deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete assignment. Please try again.'}), 500


# ─── CHANGE PASSWORD API (for teacher & student) ─────────────────────────────

@admin_bp.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Allow any logged-in user (teacher/student) to change their password."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        new_password = (data.get('new_password') or '').strip()

        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        current_user.set_password(new_password)
        db.session.commit()

        # Send email notification (best-effort)
        send_password_changed_mail(current_user.email, current_user.name, new_password)

        return jsonify({'message': 'Password changed successfully. A confirmation email has been sent.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password. Please try again.'}), 500


# ─── STATS API (for landing page dynamic counts) ─────────────────────────────

@admin_bp.route('/api/stats', methods=['GET'])
def api_stats():
    """Public endpoint to get live counts for the landing page."""
    try:
        total_students = Student.query.count()
        total_teachers = Teacher.query.count()
        total_classes = Class.query.count()
        return jsonify({
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes
        })
    except Exception as e:
        return jsonify({'total_students': 0, 'total_teachers': 0, 'total_classes': 0})
