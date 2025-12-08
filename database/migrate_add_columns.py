"""Добавляет новые колонки в таблицу персонажей."""

from database.utils import execute_sql


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


if __name__ == "__main__":
    execute_sql(SQL_STATEMENTS)
