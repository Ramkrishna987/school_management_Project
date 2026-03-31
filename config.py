import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'school-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'postgresql://postgres:Ramu%40123@localhost:5432/school_management_flask'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fix ERR_TOO_MANY_REDIRECTS on localhost:
    # SESSION_COOKIE_SECURE must be False for http (localhost).
    # If True on http, browser silently drops the cookie → login loop.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set True only when running on HTTPS

    # Flask-Mail config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'chennaramakrishna916@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'ibajqpwzvtxfipxp')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'chennaramakrishna916@gmail.com')

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
