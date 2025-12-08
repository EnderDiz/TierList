from sqlalchemy import text
from app import create_app
from models import db

app = create_app()

SQL_STATEMENTS = [
    "ALTER TABLE character ADD COLUMN balance_status TEXT",
]

with app.app_context():
    for stmt in SQL_STATEMENTS:
        try:
            db.session.execute(text(stmt))
            print("OK:", stmt)
        except Exception as e:
            print("SKIP:", stmt, "=>", e)
    db.session.commit()
    print("Миграция завершена")