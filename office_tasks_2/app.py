# app.py
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from functools import wraps

from db import (
    get_user_by_credentials,
    create_user,
    get_user_by_id,
    get_tasks_filtered,
    get_task_support_data,
    create_task,
    update_task_status,
    get_task_status_stats,
    get_all_users,
    get_all_roles,
    update_user,
    get_all_active_users,
    create_admin_user,  # <-- ИМПОРТ ДОБАВЛЕН СЮДА
)


app = Flask(__name__)
app.secret_key = "super-secret-key-change-me"  # замени в бою

# СОЗДАЁМ АДМИНИСТРАТОРА ПРИ ЗАПУСКЕ (ЭТА СТРОКА ДОЛЖНА БЫТЬ ЗДЕСЬ, С ОТСТУПОМ КАК У app)
create_admin_user()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # Неавторизованный пользователь — пустая страница с модальным окном входа
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


@app.route("/")
def index():
    """
    Корень: если не авторизован — отправляем на /login,
    если авторизован — на список задач.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("tasks"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Страница с модальным окном входа/регистрации.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = get_user_by_credentials(username, password)
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("tasks"))
        else:
            flash("Неверный логин или пароль", "error")

    # GET или ошибка логина
    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    """
    Обработка регистрации в модальном окне.
    После успешной регистрации сразу логиним пользователя.
    """
    username = request.form.get("reg_username", "").strip()
    password = request.form.get("reg_password", "").strip()
    full_name = request.form.get("reg_full_name", "").strip()
    email = request.form.get("reg_email", "").strip() or None

    if not username or not password or not full_name:
        flash("Заполните все обязательные поля.", "error")
        return redirect(url_for("login"))

    # Можно добавить проверки на длину/формат
    try:
        user_id = create_user(username, password, full_name, email)
        session["user_id"] = user_id
        return redirect(url_for("tasks"))
    except Exception as e:
        print("Error creating user:", e)
        flash("Пользователь с таким логином или email уже существует.", "error")
        return redirect(url_for("login"))


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    """
    Главная страница после входа:
    - GET: вывод списка задач с фильтрацией и поиском
    - POST: создание новой задачи
    """
    current_user = get_current_user()
    is_admin = current_user and current_user.get("role_code") == "ADMIN"

    if request.method == "POST":
        # Создание новой задачи
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status_id = request.form.get("status_id")
        priority_id = request.form.get("priority_id")
        category_id = request.form.get("category_id") or None
        due_date = request.form.get("due_date") or None
        assignee_id = request.form.get("assignee_id")

        if not title:
            flash("Название задачи обязательно.", "error")
        elif not assignee_id:
            flash("Не выбран сотрудник, на которого назначена задача.", "error")
        else:
            try:
                create_task(
                    title=title,
                    description=description,
                    creator_id=current_user["id"],
                    assignee_id=int(assignee_id),
                    status_id=int(status_id),
                    priority_id=int(priority_id),
                    category_id=int(category_id) if category_id else None,
                    due_date=due_date,
                )
                flash("Задача успешно создана.", "success")
            except Exception as e:
                print("Error creating task:", e)
                flash("Ошибка при создании задачи.", "error")

        return redirect(url_for("tasks"))

    # GET: фильтры + поиск
    view = request.args.get("view", "assigned")
    search_query = request.args.get("q", "").strip() or None

    tasks_list = get_tasks_filtered(
        user_id=current_user["id"],
        view=view,
        search=search_query,
        is_admin=is_admin,
    )
    support = get_task_support_data()
    employees = get_all_active_users()

    return render_template(
        "tasks.html",
        tasks=tasks_list,
        statuses=support["statuses"],
        priorities=support["priorities"],
        categories=support["categories"],
        employees=employees,
        current_view=view,
        search_query=search_query or "",
    )


@app.route("/admin")
@login_required
def admin_panel():
    current_user = get_current_user()
    if not current_user or current_user.get("role_code") != "ADMIN":
        flash("Доступ запрещён.", "error")
        return redirect(url_for("tasks"))

    status_stats = get_task_status_stats()
    users = get_all_users()
    roles = get_all_roles()

    return render_template(
        "admin_panel.html",
        status_stats=status_stats,
        users=users,
        roles=roles,
    )


@app.route("/admin/users/<int:user_id>/update", methods=["POST"])
@login_required
def admin_update_user(user_id):
    current_user = get_current_user()
    if not current_user or current_user.get("role_code") != "ADMIN":
        flash("Доступ запрещён.", "error")
        return redirect(url_for("tasks"))

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip() or None
    role_id = request.form.get("role_id")
    is_active = request.form.get("is_active") == "on"

    if not full_name or not role_id:
        flash("ФИО и роль обязательны.", "error")
        return redirect(url_for("admin_panel"))

    try:
        update_user(
            user_id=user_id,
            full_name=full_name,
            email=email,
            role_id=int(role_id),
            is_active=is_active,
        )
        flash("Пользователь обновлён.", "success")
    except Exception as e:
        print("Error updating user:", e)
        flash("Ошибка при обновлении пользователя.", "error")

    return redirect(url_for("admin_panel"))


@app.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def change_task_status(task_id):
    """
    Изменить статус задачи (например, отметить 'Выполнена').
    """
    status_id = request.form.get("status_id")
    if not status_id:
        flash("Не указан статус.", "error")
        return redirect(url_for("tasks"))

    current_user = get_current_user()
    is_admin = current_user and current_user.get("role_code") == "ADMIN"

    try:
        update_task_status(
            task_id=task_id,
            status_id=int(status_id),
            user_id=current_user["id"],
            is_admin=is_admin,
        )
        flash("Статус задачи обновлён.", "success")
    except Exception as e:
        print("Error updating task status:", e)
        flash("Ошибка при обновлении статуса.", "error")

    return redirect(url_for("tasks"))


@app.route("/admin/tasks/<int:task_id>/update", methods=["POST"])
@login_required
def admin_update_task(task_id):
    current_user = get_current_user()
    if not current_user or current_user.get("role_code") != "ADMIN":
        flash("Нет доступа.", "error")
        return redirect(url_for("tasks"))

    field = request.form.get("field")
    value = request.form.get("value")

    allowed = {
        "priority": "priority_id",
        "category": "category_id",
        "assignee": "assignee_id",
    }

    if field not in allowed:
        flash("Недопустимое поле.", "error")
        return redirect(url_for("tasks"))

    column = allowed[field]

    from db import connect_db

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE tasks SET {column} = %s WHERE id = %s",
                (value if value else None, task_id)
            )
            conn.commit()
    finally:
        conn.close()

    flash("Задача обновлена.", "success")
    return redirect(url_for("tasks"))


if __name__ == "__main__":
    app.run(debug=True)