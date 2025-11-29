from sqlalchemy import text
from app import create_app
from models import db

app = create_app()

SQL_STATEMENTS = [
    "ALTER TABLE character ADD COLUMN class_name TEXT",
    "ALTER TABLE character ADD COLUMN faction TEXT",
    "ALTER TABLE character ADD COLUMN tier_weapon TEXT",
    "ALTER TABLE character ADD COLUMN tier_skill TEXT",
    "ALTER TABLE character ADD COLUMN tier_passive TEXT",
    "ALTER TABLE character ADD COLUMN tier_ultimate TEXT",
    "ALTER TABLE character ADD COLUMN difficulty TEXT",
    "ALTER TABLE character ADD COLUMN short_summary TEXT",
    "ALTER TABLE character ADD COLUMN review TEXT",
    "ALTER TABLE character ADD COLUMN image_name TEXT",
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
