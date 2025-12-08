# app.py
import os
from pathlib import Path

from auth import get_current_user, login_user, logout_user, admin_required
from config import Config
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from models import db, User, Character, Skill
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Создаём служебные директории на старте, чтобы пути точно существовали
    Path(app.config["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["MEDIA_IMAGES_DIR"]).mkdir(parents=True, exist_ok=True)

    BALANCE_STATUSES: dict[str, str] = {
        "nerf": "Ослабление",
        "buff": "Усиление",
        "rework": "Переработка",
    }

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    db.init_app(app)

    @app.context_processor
    def inject_user():
        return {"current_user": get_current_user()}

    @app.before_request
    def enforce_https():
        if not app.config.get("FORCE_HTTPS"):
            return None

        is_secure = request.is_secure or request.headers.get("X-Forwarded-Proto", "").split(",")[0].strip() == "https"
        if not is_secure:
            https_url = request.url.replace("http://", "https://", 1)
            return redirect(https_url, code=301)
        return None

    @app.after_request
    def add_security_headers(response):
        if app.config.get("FORCE_HTTPS"):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @app.route("/media/images/<path:filename>")
    def media_image(filename):
        """Отдаём пользовательские изображения из отдельной папки."""

        return send_from_directory(app.config["MEDIA_IMAGES_DIR"], filename)

    def normalize_image_name(name: str | None):
        """Оставляем только базовое имя файла, чтобы можно было менять расширение."""
        if not name:
            return None
        name = name.strip()
        if not name:
            return None

        base, _ext = os.path.splitext(name)
        return base or None

    def parse_skills_form(form):
        """Читает данные из формы и собирает список словарей по навыкам."""
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
        """Возвращает доступные версии изображения из папки media/images."""

        base = normalize_image_name(image_name)
        if not base:
            return []

        images_dir = Path(app.config["MEDIA_IMAGES_DIR"])
        sources = []
        for ext, mime in (
            (".webp", "image/webp"),
            (".png", "image/png"),
            (".jpg", "image/jpeg"),
            (".jpeg", "image/jpeg"),
        ):
            candidate = images_dir / f"{base}{ext}"
            if candidate.exists():
                sources.append({"path": candidate.name, "mime": mime})
        return sources

    app.jinja_env.globals["image_sources"] = image_sources
    app.jinja_env.globals["BALANCE_STATUSES"] = BALANCE_STATUSES

    def normalize_balance_status(value: str | None):
        value = (value or "").strip().lower()
        if not value:
            return None
        return value if value in BALANCE_STATUSES else None

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
        def requested_filter(name: str):
            value = (request.args.get(name) or "*").strip() or "*"
            return value

        class_value = requested_filter("class_name")
        faction_value = requested_filter("faction")
        search = (request.args.get("search") or "").strip()

        difficulty_aliases = {"Для новичков": "Лёгкий"}

        def canonical_difficulty(value: str | None):
            value = (value or "").strip()
            if not value or value == "*":
                return None
            return difficulty_aliases.get(value, value)

        difficulty_value = (request.args.get("difficulty") or "*").strip() or "*"
        difficulty = canonical_difficulty(difficulty_value)
        active_difficulty_value = difficulty or "*"

        query = Character.query

        if class_value != "*":
            query = query.filter(Character.class_name == class_value)
        if faction_value != "*":
            query = query.filter(Character.faction == faction_value)
        if difficulty:
            difficulty_values = {difficulty}
            difficulty_values.update(
                alias for alias, canonical in difficulty_aliases.items() if canonical == difficulty
            )
            if len(difficulty_values) == 1:
                query = query.filter(Character.difficulty == difficulty)
            else:
                query = query.filter(Character.difficulty.in_(difficulty_values))
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

        raw_difficulty_values = {
            (row[0] or "").strip()
            for row in db.session
            .query(Character.difficulty)
            .filter(Character.difficulty.isnot(None))
            .distinct()
            .all()
            if (row[0] or "").strip() and (row[0] or "").strip() != "*"
        }

        normalized_difficulties = {canonical_difficulty(value) for value in raw_difficulty_values}
        normalized_difficulties.discard(None)

        preferred_order = ["Лёгкий", "Средний", "Сложный"]
        ordered_known = [name for name in preferred_order if name in normalized_difficulties]
        remaining = sorted(normalized_difficulties - set(preferred_order))
        available_difficulties = ordered_known + remaining

        difficulty_labels = {"Для новичков": "Лёгкий", "Лёгкий": "Лёгкий"}

        return render_template(
            "tier_list.html",
            tiers=tiers,
            available_classes=available_classes,
            available_factions=available_factions,
            available_difficulties=available_difficulties,
            active_class=class_value,
            active_faction=faction_value,
            active_difficulty=active_difficulty_value,
            difficulty_labels=difficulty_labels,
        )

    @app.route("/character/<slug>")
    def character_detail(slug):
        ch = Character.query.filter_by(slug=slug).first_or_404()

        # Группируем навыки по типу
        skills_by_type = {}
        for s in ch.skills:
            skills_by_type.setdefault(s.type or "Other", []).append(s)

        skill_preferences = [
            (["Пассивка", "Пассивный", "Passive", "Пассивная способность"], "Пассивный навык"),
            (["Навык", "Skill", "Обычный", "Базовый", "Активный"], "Обычный навык"),
            (["Ультимейт", "Ульта", "Ultimate", "Сигнатурный"], "Ультимативный навык"),
        ]

        used_skill_types = set()
        ordered_skill_groups = []

        for keys, label in skill_preferences:
            group_skills = []
            for key in keys:
                if key in skills_by_type and key not in used_skill_types:
                    group_skills.extend(skills_by_type[key])
                    used_skill_types.add(key)
            ordered_skill_groups.append({"label": label, "skills": group_skills})

        additional_skill_groups = [
            {"label": skill_type, "skills": skills}
            for skill_type, skills in skills_by_type.items()
            if skill_type not in used_skill_types
        ]

        return render_template(
            "character.html",
            character=ch,
            skills_by_type=skills_by_type,
            skill_groups=ordered_skill_groups,
            additional_skill_groups=additional_skill_groups,
        )

    # ------- Админка --------

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        sort = request.args.get("sort", "name")
        direction = request.args.get("direction", "asc")

        allowed_sorts = {
            "id": Character.id,
            "name": Character.name,
            "class_name": Character.class_name,
            "faction": Character.faction,
            "overall_tier": None,
        }

        if sort not in allowed_sorts:
            sort = "name"
        if direction not in ("asc", "desc"):
            direction = "asc"

        if sort == "overall_tier":
            characters = Character.query.all()
            tier_weights = {"D": 1, "C": 2, "B": 3, "A": 4, "S": 5, "SS": 6, "SSS": 7}
            none_sentinel = float("-inf") if direction == "desc" else float("inf")

            def tier_key(ch):
                value = tier_weights.get(ch.overall_tier, none_sentinel)
                return (value, ch.id)

            characters.sort(key=tier_key, reverse=direction == "desc")
        else:
            column = allowed_sorts[sort]
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

            balance_status = normalize_balance_status(
                request.form.get("balance_status")
            )

            tier_weapon = request.form.get("tier_weapon")
            tier_skill = request.form.get("tier_skill")
            tier_passive = request.form.get("tier_passive")
            tier_ultimate = request.form.get("tier_ultimate")

            difficulty = request.form.get("difficulty")  # НОВОЕ

            short_summary = request.form.get("short_summary")
            cons = request.form.get("cons")
            review = request.form.get("review")

            image_name_raw = request.form.get("image_name")
            image_name = normalize_image_name(image_name_raw)

            skills_payload = parse_skills_form(request.form)

            ch = Character(
                name=name,
                slug=slug,
                class_name=class_name,
                faction=faction,
                balance_status=balance_status,
                tier_weapon=tier_weapon,
                tier_skill=tier_skill,
                tier_passive=tier_passive,
                tier_ultimate=tier_ultimate,
                difficulty=difficulty,  # НОВОЕ
                short_summary=short_summary,
                cons=cons,
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

        wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if request.method == "POST":
            ch.name = request.form.get("name")
            ch.slug = request.form.get("slug")
            ch.class_name = request.form.get("class_name")
            ch.faction = request.form.get("faction")

            ch.balance_status = normalize_balance_status(
                request.form.get("balance_status")
            )

            ch.tier_weapon = request.form.get("tier_weapon")
            ch.tier_skill = request.form.get("tier_skill")
            ch.tier_passive = request.form.get("tier_passive")
            ch.tier_ultimate = request.form.get("tier_ultimate")

            ch.difficulty = request.form.get("difficulty")  # НОВОЕ

            ch.short_summary = request.form.get("short_summary")
            ch.cons = request.form.get("cons")
            ch.review = request.form.get("review")

            img_raw = request.form.get("image_name")
            ch.image_name = normalize_image_name(img_raw)

            skills_payload = parse_skills_form(request.form)
            payload_skills = []
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
                payload_skills.append(skill)

            for skill in list(ch.skills):
                if skill.id and str(skill.id) not in kept_ids and str(skill.id) in existing_by_id:
                    db.session.delete(skill)

            db.session.commit()
            if wants_json:
                return jsonify(
                    {
                        "status": "ok",
                        "skill_ids": [s.id for s in payload_skills],
                    }
                )

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
    ssl_cert = os.getenv("SSL_CERT_FILE")
    ssl_key = os.getenv("SSL_KEY_FILE")
    ssl_context = (ssl_cert, ssl_key) if ssl_cert and ssl_key else None

    # Делаем доступным по локальной сети
    app.run(host="0.0.0.0", port=8000, debug=False, ssl_context=ssl_context)
