"""Создание администратора через консоль."""

import sys
from pathlib import Path
from getpass import getpass

from werkzeug.security import generate_password_hash


def _ensure_project_root():
    """Make sure the repository root is importable when run as a script."""

    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


if __package__ is None or __package__ == "":
    _ensure_project_root()

from database.utils import app_context
from models import User, db


def main():
    """Запрашивает данные и создаёт пользователя с правами администратора."""

    username = input("Введите логин администратора: ")
    password = getpass("Введите пароль: ")

    with app_context():
        if User.query.filter_by(username=username).first():
            print("Такой пользователь уже существует.")
            return

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=True,
        )
        db.session.add(user)
        db.session.commit()
        print("Администратор создан.")