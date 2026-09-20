from functools import wraps
from flask import jsonify
from flask_login import current_user, login_required


def require_admin(function):
    @wraps(function)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            return jsonify(error="Administrator access required"), 403
        return function(*args, **kwargs)
    return wrapped
