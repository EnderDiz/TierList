# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    slug = db.Column(db.String(128), unique=True, nullable=False)

    class_name = db.Column(db.String(32))
    faction = db.Column(db.String(32))

    # Балансные изменения
    balance_status = db.Column(db.String(16))

    tier_weapon = db.Column(db.String(3))
    tier_skill = db.Column(db.String(3))
    tier_passive = db.Column(db.String(3))
    tier_ultimate = db.Column(db.String(3))

    difficulty = db.Column(db.String(32))  # НОВОЕ: сложность освоения

    short_summary = db.Column(db.Text)
    review = db.Column(db.Text)

    image_name = db.Column(db.String(255))

    skills = db.relationship("Skill", backref="character", lazy=True,
                             cascade="all, delete-orphan")


    @property
    def overall_tier(self):
        """Средняя оценка для группировки по тиру."""
        map_letter = {
            "D": 1,
            "C": 2,
            "B": 3,
            "A": 4,
            "S": 5,
            "SS": 6,
            "SSS": 7,
        }
        map_back = {v: k for k, v in map_letter.items()}

        vals = [
            map_letter.get(self.tier_weapon),
            map_letter.get(self.tier_skill),
            map_letter.get(self.tier_passive),
            map_letter.get(self.tier_ultimate),
        ]
        vals = [v for v in vals if v is not None]
        if not vals:
            return None

        avg = sum(vals) / len(vals)
        closest = min(map_back.keys(), key=lambda v: abs(v - avg))
        return map_back[closest]


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)

    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(32))
    description = db.Column(db.Text)
    valid_hits = db.Column(db.String(32))
    cooldown = db.Column(db.String(32))
    level_info = db.Column(db.Text)
