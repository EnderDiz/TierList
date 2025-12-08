"""Единый файл миграции для добавления поля cons в таблицу персонажей."""

import sys
from pathlib import Path

def _ensure_project_root():
    """Make sure the repository root is importable when run as a script."""

    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


if __package__ is None or __package__ == "":
    _ensure_project_root()

from database.utils import execute_sql


SQL_STATEMENTS = [
    "ALTER TABLE character ADD COLUMN cons TEXT",
]


if __name__ == "__main__":
    execute_sql(SQL_STATEMENTS)