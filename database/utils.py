"""Общие вспомогательные функции для скриптов работы с БД."""

from contextlib import contextmanager
from pathlib import Path
import sys
from typing import Iterable

# Добавляем корень проекта в sys.path, чтобы можно было импортировать app/models
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from models import db
from sqlalchemy import text


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
        print("Миграция завершена")
