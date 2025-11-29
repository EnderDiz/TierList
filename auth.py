# auth.py
from functools import wraps
from flask import session, redirect, url_for, flash
from models import User


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return User.query.get(user_id)


def login_user(user):
    session["user_id"] = user.id


def logout_user():
    session.pop("user_id", None)


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            flash("Недостаточно прав.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper
