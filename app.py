from flask import Flask, jsonify, render_template
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from models import db
from models.user import User

mail = Mail()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.common_routes import common_bp
    from routes.admin_routes import admin_bp
    from routes.teacher_routes import teacher_bp
    from routes.student_routes import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(common_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        if _wants_json():
            return jsonify({'error': 'Bad request. Please check your input.'}), 400
        return render_template('common/error.html',
                               code=400, message='Bad Request',
                               detail='The server could not understand the request.'), 400

    @app.errorhandler(403)
    def forbidden(e):
        if _wants_json():
            return jsonify({'error': 'You do not have permission to perform this action.'}), 403
        return render_template('common/error.html',
                               code=403, message='Access Denied',
                               detail='You do not have permission to view this page.'), 403

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({'error': 'Resource not found.'}), 404
        return render_template('common/error.html',
                               code=404, message='Page Not Found',
                               detail='The page you are looking for does not exist.'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        if _wants_json():
            return jsonify({'error': 'An internal server error occurred. Please try again.'}), 500
        return render_template('common/error.html',
                               code=500, message='Server Error',
                               detail='Something went wrong on our end. Please try again later.'), 500

    def _wants_json():
        from flask import request
        return request.is_json or request.path.startswith('/admin/api') or \
               request.path.startswith('/teacher/api') or request.path.startswith('/student/api')

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
