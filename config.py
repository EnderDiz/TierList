# config.py
"""Базовая конфигурация приложения."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "database"
MEDIA_IMAGES_DIR = BASE_DIR / "media" / "images"


class Config:
    # Секретный ключ оставляем для совместимости, в продакшене его нужно
    # переопределять через переменные окружения.
    SECRET_KEY = "change_this_to_random_long_string"

    # Путь до SQLite базы в отдельной директории, чтобы данные не лежали в корне
    # репозитория и их было проще игнорировать в git.
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR / 'tierlist.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Принудительное использование HTTPS при необходимости
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    PREFERRED_URL_SCHEME = "https" if FORCE_HTTPS else "http"
    SESSION_COOKIE_SECURE = FORCE_HTTPS
    REMEMBER_COOKIE_SECURE = FORCE_HTTPS
    SESSION_COOKIE_SAMESITE = "Lax"

    # Дополнительные пути для сервисов
    DATA_DIR = str(DATA_DIR)
    MEDIA_IMAGES_DIR = str(MEDIA_IMAGES_DIR)