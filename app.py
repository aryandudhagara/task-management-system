"""
app.py
------
Flask application entry point and REST API definition.

This file wires together:
- The Flask web server
- All six REST API endpoints
- A route that serves the HTML dashboard
- Automatic database initialisation on startup

Run with:
    python app.py
"""

from flask import Flask, jsonify, request, render_template, abort
from database import (
    init_db,
    create_task,
    get_all_tasks,
    get_task_by_id,
    update_task,
    complete_task,
    delete_task,
    get_task_counts,
)

# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------

app = Flask(__name__)

# Allowed values for validated fields
VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"Pending", "Completed"}


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def success_response(data, status_code: int = 200):
    """Wrap data in a consistent JSON envelope and return a Response."""
    return jsonify({"success": True, "data": data}), status_code


def error_response(message: str, status_code: int = 400):
    """Return a standardised error JSON response."""
    return jsonify({"success": False, "error": message}), status_code


def validate_task_input(data: dict, require_all: bool = True) -> str | None:
    """
    Validate incoming task JSON.

    require_all=True  → all required fields must be present (used for POST).
    require_all=False → only validate fields that are actually present (PUT).

    Returns an error message string if validation fails, or None if OK.
    """
    title = data.get("title", "").strip()
    priority = data.get("priority", "")
    status = data.get("status", "")

    if require_all:
        if not title:
            return "Task title is required and cannot be empty."
        if priority not in VALID_PRIORITIES:
            return f"Priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}."

    else:  # partial update — only validate fields that were sent
        if "title" in data and not title:
            return "Task title cannot be empty."
        if "priority" in data and priority not in VALID_PRIORITIES:
            return f"Priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}."
        if "status" in data and status not in VALID_STATUSES:
            return f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}."

    return None  # No errors


# ------------------------------------------------------------------
# Frontend route
# ------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the main HTML dashboard."""
    return render_template("index.html")


# ------------------------------------------------------------------
# API: GET /api/tasks  — list all tasks (supports query params)
# ------------------------------------------------------------------

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    """
    Retrieve all tasks.

    Optional query parameters:
      ?status=Pending|Completed
      ?priority=Low|Medium|High
      ?search=<text>

    Returns 200 with a list of task objects plus summary counts.
    """
    status_filter   = request.args.get("status")
    priority_filter = request.args.get("priority")
    search_query    = request.args.get("search")

    tasks  = get_all_tasks(status_filter, priority_filter, search_query)
    counts = get_task_counts()

    return success_response({"tasks": tasks, "counts": counts})


# ------------------------------------------------------------------
# API: GET /api/tasks/<id>  — retrieve one task
# ------------------------------------------------------------------

@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def api_get_task(task_id: int):
    """
    Retrieve a single task by its numeric ID.
    Returns 404 if the task does not exist.
    """
    task = get_task_by_id(task_id)
    if not task:
        return error_response(f"Task with ID {task_id} was not found.", 404)
    return success_response(task)


# ------------------------------------------------------------------
# API: POST /api/tasks  — create a new task
# ------------------------------------------------------------------

@app.route("/api/tasks", methods=["POST"])
def api_create_task():
    """
    Create a new task.

    Expected JSON body:
      {
        "title":       "Buy groceries",          ← required
        "description": "Milk, eggs, bread",      ← optional
        "priority":    "High",                   ← required (Low/Medium/High)
        "due_date":    "2026-12-31"              ← optional (YYYY-MM-DD)
      }

    Returns 201 Created with the new task on success.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.")

    err = validate_task_input(data, require_all=True)
    if err:
        return error_response(err)

    task = create_task(
        title       = data["title"].strip(),
        description = data.get("description", "").strip(),
        priority    = data["priority"],
        due_date    = data.get("due_date"),
    )
    return success_response(task, 201)


# ------------------------------------------------------------------
# API: PUT /api/tasks/<id>  — update a task
# ------------------------------------------------------------------

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_update_task(task_id: int):
    """
    Update an existing task's fields.

    All fields are optional — only the ones sent will be used.
    Returns 404 if the task does not exist.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.")

    existing = get_task_by_id(task_id)
    if not existing:
        return error_response(f"Task with ID {task_id} was not found.", 404)

    err = validate_task_input(data, require_all=False)
    if err:
        return error_response(err)

    # Merge: use new value if provided, otherwise keep existing
    updated = update_task(
        task_id     = task_id,
        title       = data.get("title", existing["title"]).strip(),
        description = data.get("description", existing["description"]).strip(),
        priority    = data.get("priority", existing["priority"]),
        due_date    = data.get("due_date", existing["due_date"]),
        status      = data.get("status", existing["status"]),
    )
    return success_response(updated)


# ------------------------------------------------------------------
# API: PATCH /api/tasks/<id>/complete  — mark as completed
# ------------------------------------------------------------------

@app.route("/api/tasks/<int:task_id>/complete", methods=["PATCH"])
def api_complete_task(task_id: int):
    """
    Mark a task as Completed.
    Returns 404 if the task does not exist.
    """
    task = complete_task(task_id)
    if not task:
        return error_response(f"Task with ID {task_id} was not found.", 404)
    return success_response(task)


# ------------------------------------------------------------------
# API: DELETE /api/tasks/<id>  — delete a task
# ------------------------------------------------------------------

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id: int):
    """
    Permanently delete a task by ID.
    Returns 404 if the task does not exist.
    """
    deleted = delete_task(task_id)
    if not deleted:
        return error_response(f"Task with ID {task_id} was not found.", 404)
    return success_response({"message": f"Task {task_id} deleted successfully."})


# ------------------------------------------------------------------
# API: GET /api/counts  — summary statistics
# ------------------------------------------------------------------

@app.route("/api/counts", methods=["GET"])
def api_counts():
    """Return total, pending, and completed task counts."""
    return success_response(get_task_counts())


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    # Initialise the database (creates tasks.db and the table if missing)
    init_db()
    print("[OK] Database initialised -- tasks.db is ready.")
    app.run(debug=True, use_reloader=False)
