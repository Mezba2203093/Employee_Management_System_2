import os
import secrets
from datetime import timedelta
from hmac import compare_digest
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from flask_login import current_user
from .extensions import db, login_manager, migrate


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    try:
        user = db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
    return user if user and user.is_active else None


def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv(
            "COOKIE_SECURE", "false").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"] or not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("Set SECRET_KEY and DATABASE_URL in backend/.env")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.before_request
    def check_csrf():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("csrf_token")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not expected or not compare_digest(expected, supplied):
                return jsonify(error="Invalid CSRF token; reload and retry"), 403

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    from .routes.auth import auth_bp
    from .routes.hr import hr_bp
    from .routes.attendance import attendance_bp
    from .routes.leave import leave_bp
    from .routes.reports import report_bp
    for blueprint in (auth_bp, hr_bp, attendance_bp, leave_bp, report_bp):
        app.register_blueprint(blueprint)

    from .seed import register_cli
    register_cli(app)
    return app
