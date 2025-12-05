# app.py
import os

from auth import get_current_user, login_user, logout_user, admin_required
from config import Config
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Character, Skill
from werkzeug.security import check_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    @app.context_processor
    def inject_user():
        return {"current_user": get_current_user()}

    def normalize_image_name(name: str | None):
        """Store only the base file name (no extension) for flexible formats."""
        if not name:
            return None
        name = name.strip()
        if not name:
            return None

        base, _ext = os.path.splitext(name)
        return base or None

    def parse_skills_form(form):
        names = form.getlist("skill_name")
        types = form.getlist("skill_type")
        descriptions = form.getlist("skill_description")
        cooldowns = form.getlist("skill_cooldown")
        ids = form.getlist("skill_id")

        skills = []
        for idx, name in enumerate(names):
            if not name or not name.strip():
                continue
            skills.append({
                "id": ids[idx] if idx < len(ids) else "",
                "name": name.strip(),
                "type": types[idx].strip() if idx < len(types) else None,
                "description": descriptions[idx].strip() if idx < len(descriptions) else None,
                "cooldown": cooldowns[idx].strip() if idx < len(cooldowns) else None,
            })
        return skills

    def image_sources(image_name: str | None):
        base = normalize_image_name(image_name)
        if not base:
            return []

        static_dir = app.static_folder or os.path.join(app.root_path, "static")
        sources = []
        for ext, mime in (
                (".webp", "image/webp"),
                (".png", "image/png"),
                (".jpg", "image/jpeg"),
                (".jpeg", "image/jpeg"),
        ):
            candidate = os.path.join(static_dir, "images", base + ext)
            if os.path.exists(candidate):
                sources.append({"path": "images/" + base + ext, "mime": mime})
        return sources

    app.jinja_env.globals["image_sources"] = image_sources

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
        difficulty = request.args.get("difficulty")
        search = (request.args.get("search") or "").strip()

        query = Character.query

        if class_name:
            query = query.filter(Character.class_name == class_name)
        if faction:
            query = query.filter(Character.faction == faction)
        if difficulty:
            query = query.filter(Character.difficulty == difficulty)
        if search:
            search_like = f"%{search}%"
            query = query.filter(Character.name.ilike(search_like))

        characters = query.all()

        tiers = {
            "SSS": [],
            "SS": [],
            "S": [],
            "A": [],
            "B": [],
            "C": [],
            "D": [],
            "Unranked": [],
        }
        for ch in characters:
            t = ch.overall_tier
            if t in tiers:
                tiers[t].append(ch)
            else:
                tiers["Unranked"].append(ch)

        for key in tiers:
            tiers[key] = sorted(tiers[key], key=lambda c: c.name)

        available_classes = [
            row[0]
            for row in db.session
            .query(Character.class_name)
            .filter(Character.class_name.isnot(None))
            .distinct()
            .order_by(Character.class_name)
            .all()
        ]
        available_factions = [
            row[0]
            for row in db.session
            .query(Character.faction)
            .filter(Character.faction.isnot(None))
            .distinct()
            .order_by(Character.faction)
            .all()
        ]

        available_difficulties = [
            row[0]
            for row in db.session
            .query(Character.difficulty)
            .filter(Character.difficulty.isnot(None))
            .distinct()
            .order_by(Character.difficulty)
            .all()
        ]

        available_difficulties = [
            row[0]
            for row in db.session
            .query(Character.difficulty)
            .filter(Character.difficulty.isnot(None))
            .distinct()
            .order_by(Character.difficulty)
            .all()
        ]

        return render_template(
            "tier_list.html",
            tiers=tiers,
            available_classes=available_classes,
            available_factions=available_factions,
            available_difficulties=available_difficulties,
            active_difficulty=difficulty,
        )

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
        sort = request.args.get("sort", "name")
        direction = request.args.get("direction", "asc")

        if sort not in ("id", "name"):
            sort = "name"
        if direction not in ("asc", "desc"):
            direction = "asc"

        column = Character.id if sort == "id" else Character.name
        order_clause = column.desc() if direction == "desc" else column.asc()

        characters = Character.query.order_by(order_clause, Character.id.asc()).all()
        return render_template(
            "admin_dashboard.html",
            characters=characters,
            sort=sort,
            direction=direction,
        )

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

            skills_payload = parse_skills_form(request.form)

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
            for s in skills_payload:
                ch.skills.append(Skill(
                    name=s["name"],
                    type=s.get("type"),
                    description=s.get("description"),
                    cooldown=s.get("cooldown"),
                ))
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

            skills_payload = parse_skills_form(request.form)
            existing_by_id = {str(s.id): s for s in ch.skills if s.id}
            kept_ids = set()

            for payload in skills_payload:
                skill_id = payload.pop("id", "")
                if skill_id and skill_id in existing_by_id:
                    skill = existing_by_id[skill_id]
                    kept_ids.add(skill_id)
                else:
                    skill = Skill(character=ch)
                    db.session.add(skill)

                skill.name = payload.get("name")
                skill.type = payload.get("type")
                skill.description = payload.get("description")
                skill.cooldown = payload.get("cooldown")

            for skill in list(ch.skills):
                if skill.id and str(skill.id) not in kept_ids and str(skill.id) in existing_by_id:
                    db.session.delete(skill)

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
