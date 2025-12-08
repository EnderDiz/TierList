"""Добавляет колонку с минусами персонажа."""

from database.utils import execute_sql


SQL_STATEMENTS = [
    "ALTER TABLE character ADD COLUMN cons TEXT",
]


if __name__ == "__main__":
    execute_sql(SQL_STATEMENTS)
