"""Добавляет поле balance_status в таблицу персонажей."""

from database.utils import execute_sql

SQL_STATEMENTS = [
    "ALTER TABLE character ADD COLUMN balance_status TEXT",
]


if __name__ == "__main__":
    execute_sql(SQL_STATEMENTS)
