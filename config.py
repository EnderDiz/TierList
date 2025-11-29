# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "change_this_to_random_long_string"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "tierlist.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
