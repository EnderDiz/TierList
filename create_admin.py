# create_admin.py
from getpass import getpass
from werkzeug.security import generate_password_hash

from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    username = input("Введите логин администратора: ")
    password = getpass("Введите пароль: ")

    if User.query.filter_by(username=username).first():
        print("Такой пользователь уже существует.")
    else:
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        print("Администратор создан.")
