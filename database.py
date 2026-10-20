"""
database.py
-----------
Handles all SQLite database operations for the Task Management System.

This module provides:
- Database initialisation (creating the tasks table)
- A helper to open a connection
- CRUD functions called by the Flask API routes

Why SQLite?
- Zero configuration — no separate server needed.
- The database is a single file (tasks.db) that lives in the project folder.
- Python ships with the `sqlite3` module, so no extra install is required.
"""

import sqlite3
from datetime import datetime, timezone

# Path to the production database file
DB_PATH = "tasks.db"


def get_db(db_path: str = None) -> sqlite3.Connection:
    """
    Open and return a new SQLite connection.

    If db_path is not given, the module-level DB_PATH is used.  Reading it
    inside the function body (rather than as a default argument) means that
    monkey-patching `database.DB_PATH` at test time takes effect immediately.

    row_factory = sqlite3.Row lets us access columns by name (row["title"])
    instead of position (row[1]), which is much more readable.
    """
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = None) -> None:
    """
    Create the tasks table if it does not already exist.

    Called automatically when the Flask app starts so the database is
    always ready without any manual setup step.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    # Use parameterised SQL throughout to prevent SQL injection.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT,
            priority    TEXT    NOT NULL DEFAULT 'Medium',
            due_date    TEXT,
            status      TEXT    NOT NULL DEFAULT 'Pending',
            created_at  TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def create_task(title: str, description: str, priority: str,
                due_date: str, db_path: str = None) -> dict:
    """
    Insert a new task row and return it as a dictionary.

    Parameters are passed into the query as a tuple — never via string
    formatting — to guard against SQL injection.
    """
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tasks (title, description, priority, due_date, status, created_at)
        VALUES (?, ?, ?, ?, 'Pending', ?)
        """,
        (title, description or "", priority, due_date or None, created_at),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return get_task_by_id(new_id, db_path)


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_all_tasks(status_filter: str = None, priority_filter: str = None,
                  search: str = None, db_path: str = None) -> list[dict]:
    """
    Return all tasks as a list of dicts, with optional filtering.

    - status_filter  : 'Pending' | 'Completed'
    - priority_filter: 'Low' | 'Medium' | 'High'
    - search         : substring to look for in the title (case-insensitive)
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    if priority_filter:
        query += " AND priority = ?"
        params.append(priority_filter)

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_task_by_id(task_id: int, db_path: str = None) -> dict | None:
    """Return a single task dict by its primary key, or None if not found."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_task(task_id: int, title: str, description: str,
                priority: str, due_date: str, status: str,
                db_path: str = None) -> dict | None:
    """
    Update all editable fields of an existing task.
    Returns the updated task dict, or None if the ID was not found.
    """
    if not get_task_by_id(task_id, db_path):
        return None

    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tasks
        SET title = ?, description = ?, priority = ?, due_date = ?, status = ?
        WHERE id = ?
        """,
        (title, description or "", priority, due_date or None, status, task_id),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id, db_path)


def complete_task(task_id: int, db_path: str = None) -> dict | None:
    """
    Set a task's status to 'Completed'.
    Returns the updated task dict, or None if the ID was not found.
    """
    if not get_task_by_id(task_id, db_path):
        return None

    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status = 'Completed' WHERE id = ?",
        (task_id,),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id, db_path)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_task(task_id: int, db_path: str = None) -> bool:
    """
    Delete a task by ID.
    Returns True if a row was deleted, False if the ID did not exist.
    """
    if not get_task_by_id(task_id, db_path):
        return False

    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------------------

def get_task_counts(db_path: str = None) -> dict:
    """Return a dict with total, pending, and completed task counts."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'")
    completed = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "pending": pending, "completed": completed}
