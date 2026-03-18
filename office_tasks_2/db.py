# db.py
import pymysql
from pymysql.cursors import DictCursor


def connect_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="office_tasks",
        port=3306,
        cursorclass=DictCursor
    )


def get_user_by_id(user_id: int):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.*,
                       r.code AS role_code,
                       r.name AS role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = %s
                """,
                (user_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_credentials(username: str, password: str):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            # Исправлено: password_hash вместо password
            cur.execute(
                "SELECT * FROM users WHERE username = %s AND password_hash = %s AND is_active = 1",
                (username, password)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_username(username: str):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    finally:
        conn.close()


def create_user(username: str, password: str, full_name: str, email: str = None):
    """
    Создаём пользователя с ролью 'USER'
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            # Получаем id роли USER
            cur.execute("SELECT id FROM roles WHERE code = 'USER'")
            role = cur.fetchone()
            if not role:
                # На всякий случай создадим роль, если её нет
                cur.execute(
                    "INSERT INTO roles (code, name) VALUES ('USER', 'Сотрудник')"
                )
                conn.commit()
                cur.execute("SELECT id FROM roles WHERE code = 'USER'")
                role = cur.fetchone()

            role_id = role["id"]

            # Исправлено: password_hash вместо password
            cur.execute(
                """
                INSERT INTO users (username, password_hash, full_name, email, role_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (username, password, full_name, email, role_id)
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_task_lists_for_user(user_id: int):
    """
    Получить задачи, назначенные на пользователя.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id,
                       t.title,
                       t.description,
                       t.due_date,
                       t.created_at,
                       ts.name       AS status_name,
                       tp.name       AS priority_name,
                       tc.name       AS category_name
                FROM tasks t
                JOIN task_statuses ts ON t.status_id = ts.id
                JOIN task_priorities tp ON t.priority_id = tp.id
                LEFT JOIN task_categories tc ON t.category_id = tc.id
                WHERE t.assignee_id = %s
                ORDER BY t.due_date IS NULL, t.due_date, t.created_at DESC
                """,
                (user_id,)
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_task_support_data():
    """
    Справочники для формы создания задачи: статусы, приоритеты, категории.
    """
    conn = connect_db()
    data = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM task_statuses ORDER BY sort_order")
            data["statuses"] = cur.fetchall()

            cur.execute("SELECT * FROM task_priorities ORDER BY sort_order")
            data["priorities"] = cur.fetchall()

            cur.execute("SELECT * FROM task_categories ORDER BY name")
            data["categories"] = cur.fetchall()
        return data
    finally:
        conn.close()


def create_task(title: str, description: str, creator_id: int,
                assignee_id: int, status_id: int, priority_id: int,
                category_id: int = None, due_date: str = None):
    """
    Создать задачу. due_date ожидается в формате 'YYYY-MM-DD' или None.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks
                    (title, description, creator_id, assignee_id,
                     status_id, priority_id, category_id, due_date, is_personal)
                VALUES (%s, %s, %s, %s, %s, %s,
                        %s, %s, 1)
                """,
                (title, description, creator_id, assignee_id,
                 status_id, priority_id, category_id, due_date)
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def update_task_status(task_id: int, status_id: int, user_id: int, is_admin: bool = False):
    """
    Обновить статус задачи.
    - Обычный сотрудник: может менять только задачи, назначенные на него.
    - Администратор: может менять статус любой задачи.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            if is_admin:
                # Админ — без проверки assignee_id
                cur.execute(
                    """
                    UPDATE tasks
                    SET status_id = %s,
                        completed_at = CASE
                            WHEN %s = (SELECT id FROM task_statuses WHERE code = 'DONE')
                            THEN NOW()
                            ELSE completed_at
                        END
                    WHERE id = %s
                    """,
                    (status_id, status_id, task_id)
                )
            else:
                # Обычный сотрудник — только свои задачи
                cur.execute(
                    """
                    UPDATE tasks
                    SET status_id = %s,
                        completed_at = CASE
                            WHEN %s = (SELECT id FROM task_statuses WHERE code = 'DONE')
                            THEN NOW()
                            ELSE completed_at
                        END
                    WHERE id = %s AND assignee_id = %s
                    """,
                    (status_id, status_id, task_id, user_id)
                )
            conn.commit()
    finally:
        conn.close()


def get_task_status_stats():
    """
    Статистика по задачам: сколько задач в каждом статусе.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    ts.id,
                    ts.code,
                    ts.name,
                    COUNT(t.id) AS task_count
                FROM task_statuses ts
                LEFT JOIN tasks t ON t.status_id = ts.id
                GROUP BY ts.id, ts.code, ts.name
                ORDER BY ts.sort_order
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_all_users():
    """
    Все пользователи с ролями — для таблицы в админке.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.id,
                    u.username,
                    u.full_name,
                    u.email,
                    u.is_active,
                    u.created_at,
                    r.id AS role_id,
                    r.code AS role_code,
                    r.name AS role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.id
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_all_roles():
    """
    Все роли — для выпадающего списка в админке.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, code, name FROM roles ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()


def update_user(user_id: int, full_name: str, email: str, role_id: int, is_active: bool):
    """
    Обновление пользователя из админки.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET full_name = %s,
                    email = %s,
                    role_id = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (full_name, email, role_id, 1 if is_active else 0, user_id)
            )
            conn.commit()
    finally:
        conn.close()


def get_all_active_users():
    """
    Список активных пользователей для поля 'Сотрудник' при создании задачи.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name 
                FROM users
                WHERE is_active = 1
                ORDER BY full_name
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_tasks_filtered(user_id: int, view: str = "assigned",
                       search: str | None = None,
                       is_admin: bool = False):
    """
    Получить задачи с учётом:
    - view: 'assigned' (назначенные мне), 'created' (созданные мной), 'all' (все задачи, только для админа)
    - search: строка поиска по id, title, description
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            base_sql = """
                SELECT
                    t.id,
                    t.title,
                    t.description,
                    t.due_date,
                    t.created_at,
                    ts.name AS status_name,
                    ts.code AS status_code,
                    tp.name AS priority_name,
                    tp.code AS priority_code,
                    tc.name AS category_name,
                    c.full_name AS creator_name,
                    a.full_name AS assignee_name
                FROM tasks t
                JOIN task_statuses ts ON t.status_id = ts.id
                JOIN task_priorities tp ON t.priority_id = tp.id
                LEFT JOIN task_categories tc ON t.category_id = tc.id
                JOIN users c ON t.creator_id = c.id
                JOIN users a ON t.assignee_id = a.id
                WHERE 1=1
            """

            params = []

            # Фильтр по режиму просмотра
            if view == "created":
                base_sql += " AND t.creator_id = %s"
                params.append(user_id)
            elif view == "assigned":
                base_sql += " AND t.assignee_id = %s"
                params.append(user_id)
            elif view == "all":
                if not is_admin:
                    # не админ — всё равно только назначенные мне
                    base_sql += " AND t.assignee_id = %s"
                    params.append(user_id)
                else:
                    # админ — без доп. фильтра
                    pass
            else:
                # по умолчанию — назначенные мне
                base_sql += " AND t.assignee_id = %s"
                params.append(user_id)

            # Поиск по id, title, description
            if search:
                base_sql += """
                    AND (
                        t.id = %s
                        OR t.title LIKE %s
                        OR t.description LIKE %s
                    )
                """
                # Попробуем использовать поисковую строку как id
                params.append(search)  # для t.id = %s (MySQL сам приведёт тип)
                like = f"%{search}%"
                params.append(like)
                params.append(like)

            base_sql += """
                ORDER BY
                    t.due_date IS NULL,
                    t.due_date,
                    t.created_at DESC
            """

            cur.execute(base_sql, tuple(params))
            return cur.fetchall()
    finally:
        conn.close()


def create_admin_user():
    """
    Создать первого администратора, если пользователей нет
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            # Проверим, есть ли вообще пользователи
            cur.execute("SELECT COUNT(*) as count FROM users")
            result = cur.fetchone()
            count = result['count'] if result else 0

            if count == 0:
                print("Создаём первого администратора...")

                # Получаем id роли ADMIN
                cur.execute("SELECT id FROM roles WHERE code = 'ADMIN'")
                role = cur.fetchone()

                if role:
                    admin_role_id = role['id']

                    # Исправлено: password_hash вместо password
                    cur.execute(
                        """
                        INSERT INTO users 
                        (username, password_hash, full_name, email, role_id, is_active) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        ('admin', 'admin123', 'Главный администратор', 'admin@office.local', admin_role_id, 1)
                    )
                    conn.commit()
                    print("✓ Администратор создан: логин 'admin', пароль 'admin123'")

                    # Создаём тестового пользователя
                    cur.execute("SELECT id FROM roles WHERE code = 'USER'")
                    user_role = cur.fetchone()
                    if user_role:
                        user_role_id = user_role['id']
                        # Исправлено: password_hash вместо password
                        cur.execute(
                            """
                            INSERT INTO users 
                            (username, password_hash, full_name, email, role_id, is_active) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            ('user', 'user123', 'Тестовый сотрудник', 'user@office.local', user_role_id, 1)
                        )
                        conn.commit()
                        print("✓ Тестовый пользователь создан: логин 'user', пароль 'user123'")
                else:
                    print("Ошибка: роль ADMIN не найдена в базе данных")
            else:
                print(f"В базе уже есть {count} пользователей")
    finally:
        conn.close()