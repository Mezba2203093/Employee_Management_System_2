import secrets
from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/csrf")
def csrf():
    session["csrf_token"] = secrets.token_urlsafe(32)
    return jsonify(csrf_token=session["csrf_token"])


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "").strip().lower())
    user = db.session.execute(db.select(User).filter_by(
        email=email)).scalar_one_or_none()
    if not user or not user.is_active or not check_password_hash(
        user.password_hash, str(data.get("password", ""))
    ):
        return jsonify(error="Invalid credentials"), 401
    login_user(user)
    session.permanent = True
    return jsonify(id=user.id, role=user.role, email=user.email)


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(id=current_user.id, role=current_user.role, email=current_user.email)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return jsonify(message="Logged out")
