"""Общие вспомогательные функции для скриптов работы с БД."""

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from sqlalchemy import text

def _ensure_project_root():
    """Make sure the repository root is importable when run as a script."""

    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


if __package__ is None or __package__ == "":
    _ensure_project_root()

from app import create_app
from models import db


@contextmanager
def app_context():
    """Даёт контекст приложения Flask, чтобы использовать модели и БД."""

    app = create_app()
    with app.app_context():
        yield app


def execute_sql(statements: Iterable[str]):
    """Запускает набор SQL-выражений последовательно и печатает результат."""

    with app_context():
        for stmt in statements:
            try:
                db.session.execute(text(stmt))
                print("OK:", stmt)
            except Exception as exc:  # noqa: BLE001
                print("SKIP:", stmt, "=>", exc)
        db.session.commit()