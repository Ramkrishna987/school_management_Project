from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models import db
import secrets

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('common.dashboard'))
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            if not email or not password:
                flash('Please enter both email and password.', 'warning')
                return render_template('common/login.html')
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('common.dashboard'))
            flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
    return render_template('common/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
    except Exception:
        pass
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password — generates a temporary password and shows it on screen
    (email sending is optional/best-effort)."""
    if current_user.is_authenticated:
        return redirect(url_for('common.dashboard'))
    if request.method == 'POST':
        try:
            email = (request.form.get('email') or '').strip().lower()
            if not email:
                flash('Please enter your email address.', 'warning')
                return render_template('common/forgot_password.html')
            user = User.query.filter_by(email=email).first()
            if not user:
                # Don't reveal whether the email exists
                flash('If that email is registered, a temporary password has been sent.', 'info')
                return render_template('common/forgot_password.html')
            # Generate a secure temporary password
            temp_password = secrets.token_urlsafe(8)
            user.set_password(temp_password)
            db.session.commit()
            # Try to email; fall back to showing on screen
            email_sent = _try_send_reset_email(user.email, user.name, temp_password)
            if email_sent:
                flash('A temporary password has been sent to your email. '
                      'Please login and change your password immediately.', 'success')
            else:
                flash(f'Your temporary password is: <strong>{temp_password}</strong> &nbsp;'
                      f'— Please login and change it immediately.', 'warning')
        except Exception as e:
            flash('An error occurred. Please try again or contact your administrator.', 'danger')
        return render_template('common/forgot_password.html')
    return render_template('common/forgot_password.html')


def _try_send_reset_email(email, name, temp_password):
    """Returns True if email was sent successfully, False otherwise."""
    try:
        from flask_mail import Message
        from app import mail
        msg = Message(
            subject='EduManage — Password Reset',
            recipients=[email],
            html=f"""
            <p>Hello <strong>{name}</strong>,</p>
            <p>A password reset was requested for your account.</p>
            <p>Your temporary password is: <strong>{temp_password}</strong></p>
            <p>Please <a href="#">login</a> with this password and change it immediately.</p>
            <p>If you did not request this reset, please contact your school administrator.</p>
            """
        )
        mail.send(msg)
        return True
    except Exception:
        return False
