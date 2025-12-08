"""Создание администратора через консоль."""

from getpass import getpass

from werkzeug.security import generate_password_hash

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


if __name__ == "__main__":
    main()
