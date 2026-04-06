import sqlite3
from typing import Optional

DATABASE_USERS = "users.db"
DATABASE_TODOS = "todos.db"


def get_users_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_USERS)
    conn.row_factory = sqlite3.Row
    return conn


def get_todos_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_TODOS)
    conn.row_factory = sqlite3.Row
    return conn


def create_users_table() -> None:
    conn = get_users_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    conn.commit()
    conn.close()


def create_todos_table() -> None:
    conn = get_todos_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def init_db() -> None:
    create_users_table()
    create_todos_table()


# === CRUD для пользователей ===

def create_user(username: str, password: str, role: str = "user") -> Optional[dict]:
    conn = get_users_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    conn = get_users_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


# === CRUD для Todo ===

def create_todo(title: str, description: Optional[str] = None, completed: bool = False) -> dict:
    conn = get_todos_connection()
    cursor = conn.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (title, description, completed)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


def get_todo_by_id(todo_id: int) -> Optional[dict]:
    conn = get_todos_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_todos() -> list:
    conn = get_todos_connection()
    rows = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_todo(todo_id: int, title: Optional[str] = None, description: Optional[str] = None, completed: Optional[bool] = None) -> Optional[dict]:
    conn = get_todos_connection()
    existing = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not existing:
        conn.close()
        return None

    update_title = title if title is not None else existing["title"]
    update_desc = description if description is not None else existing["description"]
    update_completed = completed if completed is not None else bool(existing["completed"])

    conn.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (update_title, update_desc, update_completed, todo_id)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_todo(todo_id: int) -> bool:
    conn = get_todos_connection()
    cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
