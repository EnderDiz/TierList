# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Character, Skill
from auth import get_current_user, login_user, logout_user, admin_required
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    @app.context_processor
    def inject_user():
        return {"current_user": get_current_user()}

    def normalize_image_name(name: str | None):
        if not name:
            return None
        name = name.strip()
        if not name:
            return None
        if not name.lower().endswith(".png"):
            name += ".png"
        return name

    def normalize_image_name(name: str | None):
        if not name:
            return None
        name = name.strip()
        if not name:
            return None

        base, ext = os.path.splitext(name)
        # base = 'file', ext = '.jpg'
        return base + ".png"

    # ------- Маршруты --------

    @app.route("/")
    def index():
        return redirect(url_for("tier_list"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Вы вошли.", "success")
                return redirect(url_for("tier_list"))
            else:
                flash("Неверный логин или пароль.", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        logout_user()
        flash("Вы вышли.", "success")
        return redirect(url_for("login"))

    @app.route("/tier-list")
    def tier_list():
        class_name = request.args.get("class_name")
        faction = request.args.get("faction")
        search = request.args.get("search")

        query = Character.query

        if class_name:
            query = query.filter(Character.class_name == class_name)
        if faction:
            query = query.filter(Character.faction == faction)
        if search:
            search_like = f"%{search}%"
            query = query.filter(Character.name.ilike(search_like))

        characters = query.all()

        tiers = {"S": [], "A": [], "B": [], "C": [], "D": [], "Unranked": []}
        for ch in characters:
            t = ch.overall_tier
            if t in tiers:
                tiers[t].append(ch)
            else:
                tiers["Unranked"].append(ch)

        for key in tiers:
            tiers[key] = sorted(tiers[key], key=lambda c: c.name)

        return render_template("tier_list.html", tiers=tiers)

    @app.route("/character/<slug>")
    def character_detail(slug):
        ch = Character.query.filter_by(slug=slug).first_or_404()

        # Группируем навыки по типу
        skills_by_type = {}
        for s in ch.skills:
            skills_by_type.setdefault(s.type or "Other", []).append(s)

        return render_template(
            "character.html",
            character=ch,
            skills_by_type=skills_by_type
        )

    # ------- Админка --------

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        characters = Character.query.order_by(Character.name).all()
        return render_template("admin_dashboard.html", characters=characters)

    @app.route("/admin/character/new", methods=["GET", "POST"])
    @admin_required
    def admin_new_character():
        if request.method == "POST":
            name = request.form.get("name")
            slug = request.form.get("slug")
            class_name = request.form.get("class_name")
            faction = request.form.get("faction")

            tier_weapon = request.form.get("tier_weapon")
            tier_skill = request.form.get("tier_skill")
            tier_passive = request.form.get("tier_passive")
            tier_ultimate = request.form.get("tier_ultimate")

            difficulty = request.form.get("difficulty")  # НОВОЕ

            short_summary = request.form.get("short_summary")
            review = request.form.get("review")

            image_name_raw = request.form.get("image_name")
            image_name = normalize_image_name(image_name_raw)

            ch = Character(
                name=name,
                slug=slug,
                class_name=class_name,
                faction=faction,
                tier_weapon=tier_weapon,
                tier_skill=tier_skill,
                tier_passive=tier_passive,
                tier_ultimate=tier_ultimate,
                difficulty=difficulty,  # НОВОЕ
                short_summary=short_summary,
                review=review,
                image_name=image_name,
            )
            db.session.add(ch)
            db.session.commit()
            flash("Персонаж создан.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_edit_character.html", character=None)

    @app.route("/admin/character/<int:char_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_edit_character(char_id):
        ch = Character.query.get_or_404(char_id)

        if request.method == "POST":
            ch.name = request.form.get("name")
            ch.slug = request.form.get("slug")
            ch.class_name = request.form.get("class_name")
            ch.faction = request.form.get("faction")

            ch.tier_weapon = request.form.get("tier_weapon")
            ch.tier_skill = request.form.get("tier_skill")
            ch.tier_passive = request.form.get("tier_passive")
            ch.tier_ultimate = request.form.get("tier_ultimate")

            ch.difficulty = request.form.get("difficulty")  # НОВОЕ

            ch.short_summary = request.form.get("short_summary")
            ch.review = request.form.get("review")

            img_raw = request.form.get("image_name")
            ch.image_name = normalize_image_name(img_raw)

            db.session.commit()
            flash("Персонаж сохранён.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_edit_character.html", character=ch)

    @app.route("/admin/character/<int:char_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_character(char_id):
        ch = Character.query.get_or_404(char_id)
        db.session.delete(ch)
        db.session.commit()
        flash("Персонаж удалён.", "success")
        return redirect(url_for("admin_dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    # Делаем доступным по локальной сети
    app.run(host="0.0.0.0", port=8000, debug=True)
