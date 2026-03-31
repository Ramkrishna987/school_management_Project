from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.assignment import TeacherAssignment
from models.student import Student
from models.marks import Mark
from models.user import User

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated


@teacher_bp.route('/marks')
@login_required
@teacher_required
def marks_page():
    try:
        teacher = current_user.teacher
        assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
        return render_template('teacher/marks.html', assignments=assignments)
    except Exception as e:
        return render_template('teacher/marks.html', assignments=[])


@teacher_bp.route('/api/assignment/<int:aid>/students')
@login_required
@teacher_required
def api_assignment_students(aid):
    try:
        teacher = current_user.teacher
        assignment = TeacherAssignment.query.filter_by(id=aid, teacher_id=teacher.id).first_or_404()
        students = Student.query.filter_by(class_id=assignment.class_id).join(User).all()
        result = []
        for s in students:
            mark = Mark.query.filter_by(
                student_id=s.id,
                assignment_id=assignment.id
            ).first()
            result.append({
                'student_id': s.id,
                'name': s.user.name,
                'roll_number': s.roll_number or '',
                'marks': mark.marks if mark else '',
                'max_marks': mark.max_marks if mark else 100,
                'exam_type': mark.exam_type if mark else 'Unit Test',
                'mark_id': mark.id if mark else None
            })
        return jsonify({
            'students': result,
            'class_name': f"{assignment.class_.class_name}-{assignment.class_.section}",
            'subject_name': assignment.subject.subject_name
        })
    except Exception as e:
        return jsonify({'error': 'Failed to load students for this assignment. Please try again.'}), 500


@teacher_bp.route('/api/marks', methods=['POST'])
@login_required
@teacher_required
def api_save_marks():
    try:
        teacher = current_user.teacher
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        assignment_id = data.get('assignment_id')
        marks_data = data.get('marks', [])

        if not assignment_id:
            return jsonify({'error': 'Assignment ID is required'}), 400

        assignment = TeacherAssignment.query.filter_by(
            id=assignment_id, teacher_id=teacher.id).first_or_404()

        saved_count = 0
        for entry in marks_data:
            try:
                student_id = entry.get('student_id')
                marks_val = entry.get('marks')
                max_marks = entry.get('max_marks', 100)
                exam_type = entry.get('exam_type', 'Unit Test')

                if marks_val is None or marks_val == '':
                    continue

                marks_val = float(marks_val)
                if marks_val < 0:
                    continue
                if marks_val > float(max_marks):
                    return jsonify({'error': f'Marks cannot exceed max marks ({max_marks})'}), 400

                existing = Mark.query.filter_by(
                    student_id=student_id, assignment_id=assignment_id).first()

                if existing:
                    existing.marks = marks_val
                    existing.max_marks = max_marks
                    existing.exam_type = exam_type
                else:
                    mark = Mark(
                        student_id=student_id,
                        subject_id=assignment.subject_id,
                        class_id=assignment.class_id,
                        teacher_id=teacher.id,
                        assignment_id=assignment_id,
                        marks=marks_val,
                        max_marks=max_marks,
                        exam_type=exam_type
                    )
                    db.session.add(mark)
                saved_count += 1
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid marks value. Please enter valid numbers.'}), 400

        db.session.commit()
        return jsonify({'message': f'Marks saved successfully ({saved_count} records updated)'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save marks. Please try again.'}), 500
