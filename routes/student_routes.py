from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models.marks import Mark

student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            return redirect(url_for('common.dashboard'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/profile')
@login_required
@student_required
def profile():
    try:
        student = current_user.student
        if not student:
            flash('Student profile not found. Please contact your administrator.', 'warning')
            return redirect(url_for('common.dashboard'))
        return render_template('student/profile.html', student=student)
    except Exception:
        flash('An error occurred loading your profile. Please try again.', 'danger')
        return redirect(url_for('common.dashboard'))


@student_bp.route('/marks')
@login_required
@student_required
def marks():
    try:
        student = current_user.student
        if not student:
            flash('Student profile not found. Please contact your administrator.', 'warning')
            return redirect(url_for('common.dashboard'))
        marks_list = Mark.query.filter_by(student_id=student.id).all()
        total = sum(m.marks for m in marks_list)
        max_total = sum(m.max_marks for m in marks_list)
        percentage = round((total / max_total * 100), 2) if max_total else 0
        return render_template('student/marks.html', marks=marks_list,
                               percentage=percentage, student=student)
    except Exception:
        flash('An error occurred loading your marks. Please try again.', 'danger')
        return redirect(url_for('common.dashboard'))
