-- Создаем базу данных
CREATE DATABASE IF NOT EXISTS office_tasks
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE office_tasks;

-- Таблица ролей пользователей
CREATE TABLE roles (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(50) NOT NULL UNIQUE,  -- 'ADMIN', 'USER'
    name        VARCHAR(100) NOT NULL        -- 'Администратор', 'Сотрудник'
) ENGINE=InnoDB;

-- Таблица пользователей (сотрудников офиса)
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(100) UNIQUE,
    role_id         INT NOT NULL,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id) REFERENCES roles(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Таблица статусов задач
CREATE TABLE task_statuses (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(50) NOT NULL UNIQUE,   -- 'NEW', 'IN_PROGRESS', 'DONE', 'CANCELED'
    name        VARCHAR(100) NOT NULL,         -- 'Новая', 'В работе', ...
    sort_order  INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- Таблица приоритетов задач
CREATE TABLE task_priorities (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(50) NOT NULL UNIQUE,   -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    name        VARCHAR(100) NOT NULL,         -- 'Низкий', 'Средний', ...
    sort_order  INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- Таблица категорий задач
CREATE TABLE task_categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,         -- 'Рабочее', 'Личное', ...
    description VARCHAR(255),
    color       VARCHAR(20)                    -- условный цвет для UI, например '#3498db'
) ENGINE=InnoDB;

-- Таблица задач
CREATE TABLE tasks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    creator_id      INT NOT NULL,              -- кто создал
    assignee_id     INT NOT NULL,              -- на кого назначена задача
    status_id       INT NOT NULL,
    priority_id     INT NOT NULL,
    category_id     INT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
    due_date        DATE,
    completed_at    DATETIME,
    is_personal     TINYINT(1) NOT NULL DEFAULT 1,   -- личная/общая (если решишь расширять идею)

    CONSTRAINT fk_tasks_creator
        FOREIGN KEY (creator_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_assignee
        FOREIGN KEY (assignee_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_status
        FOREIGN KEY (status_id) REFERENCES task_statuses(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_priority
        FOREIGN KEY (priority_id) REFERENCES task_priorities(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_category
        FOREIGN KEY (category_id) REFERENCES task_categories(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Индексы для ускорения выборок по задачам
CREATE INDEX idx_tasks_assignee ON tasks (assignee_id);
CREATE INDEX idx_tasks_status ON tasks (status_id);
CREATE INDEX idx_tasks_due_date ON tasks (due_date);

-- Таблица комментариев к задачам
CREATE TABLE comments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    task_id     INT NOT NULL,
    user_id     INT NOT NULL,
    text        TEXT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_comments_task
        FOREIGN KEY (task_id) REFERENCES tasks(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Таблица вложений (файлов) к задачам
CREATE TABLE attachments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    task_id         INT NOT NULL,
    original_name   VARCHAR(255) NOT NULL,     -- имя файла, как у пользователя
    stored_name     VARCHAR(255) NOT NULL,     -- имя файла на сервере
    file_path       VARCHAR(255) NOT NULL,     -- относительный путь
    uploaded_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attachments_task
        FOREIGN KEY (task_id) REFERENCES tasks(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------
-- Первичное наполнение справочников
-- -----------------------------

INSERT INTO roles (code, name) VALUES
  ('ADMIN', 'Администратор'),
  ('USER',  'Сотрудник');

INSERT INTO task_statuses (code, name, sort_order) VALUES
  ('NEW',         'Новая',       1),
  ('IN_PROGRESS', 'В работе',    2),
  ('ON_HOLD',     'Ожидает',     3),
  ('DONE',        'Выполнена',   4),
  ('CANCELED',    'Отменена',    5);

INSERT INTO task_priorities (code, name, sort_order) VALUES
  ('LOW',      'Низкий',   1),
  ('MEDIUM',   'Средний',  2),
  ('HIGH',     'Высокий',  3),
  ('CRITICAL', 'Критичный',4);

INSERT INTO task_categories (name, description, color) VALUES
  ('Рабочие',   'Рабочие задачи и поручения', '#3498db'),
  ('Личные',    'Личные дела сотрудника',     '#2ecc71'),
  ('Обучение',  'Курсы, вебинары, саморазвитие', '#9b59b6');

