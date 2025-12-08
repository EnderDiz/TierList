# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "change_this_to_random_long_string"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "tierlist.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    PREFERRED_URL_SCHEME = "https" if FORCE_HTTPS else "http"
    SESSION_COOKIE_SECURE = FORCE_HTTPS
    REMEMBER_COOKIE_SECURE = FORCE_HTTPS
    SESSION_COOKIE_SAMESITE = "Lax"