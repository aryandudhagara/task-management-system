# Task Management System

A clean, full-stack **Task Management web application** built with Python, Flask, SQLite, HTML, CSS, and vanilla JavaScript. Designed as a portfolio-quality project demonstrating REST API development, SQL database management, and frontend/backend integration — without any heavyweight frameworks.

---

## ✨ Features

- **Full CRUD** — Create, Read, Update, and Delete tasks
- **Mark Complete** — One-click task completion
- **Smart Filtering** — Filter by status (Pending / Completed) and priority (Low / Medium / High)
- **Live Search** — Instantly search tasks by title (debounced)
- **Summary Dashboard** — Cards showing total, pending, and completed counts
- **Input Validation** — Both server-side (Flask) and client-side (JavaScript)
- **Consistent REST API** — JSON responses with meaningful status codes
- **Automated Tests** — 8 `unittest` tests with an isolated in-memory database

---

## 🗂 Project Structure

```
task-management-system/
├── app.py              # Flask app + all REST API routes
├── database.py         # SQLite helper functions (CRUD, parameterised SQL)
├── requirements.txt    # Python dependencies (Flask only)
├── .gitignore
├── README.md
├── templates/
│   └── index.html      # Single-page dashboard
├── static/
│   ├── style.css       # Dark glassmorphism design system
│   └── script.js       # Vanilla JS frontend (fetch API)
└── tests/
    └── test_api.py     # unittest suite
```

---

## ⚙️ Setup Instructions (Windows PowerShell)

### 1. Check Python is installed
```powershell
python --version
```
You need Python 3.10 or later.  Download from https://python.org if needed.

### 2. Navigate to the project folder
```powershell
cd path\to\task-management-system
```

### 3. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you see a security error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. Install dependencies
```powershell
pip install -r requirements.txt
```

### 5. Run the application
```powershell
python app.py
```

The database (`tasks.db`) is created automatically on first run.

### 6. Open in your browser
Visit: **http://127.0.0.1:5000**

---

## 🧪 Running Automated Tests

With the virtual environment activated:
```powershell
python -m unittest tests/test_api.py -v
```

All 8 tests use an isolated in-memory database — no production data is touched.

---

## 🌐 REST API Reference

Base URL: `http://127.0.0.1:5000`

All responses follow this envelope:
```json
{ "success": true, "data": { ... } }
{ "success": false, "error": "message" }
```

### GET /api/tasks
Retrieve all tasks (supports `?status=`, `?priority=`, `?search=` query params).

```http
GET /api/tasks?status=Pending&priority=High
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": 1,
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "priority": "High",
        "due_date": "2026-12-31",
        "status": "Pending",
        "created_at": "2026-10-11 18:00:00"
      }
    ],
    "counts": { "total": 5, "pending": 3, "completed": 2 }
  }
}
```

---

### GET /api/tasks/{id}
Retrieve a single task.

Response `200` or `404`:
```json
{ "success": false, "error": "Task with ID 99 was not found." }
```

---

### POST /api/tasks
Create a new task.

Request body:
```json
{
  "title":       "Buy groceries",
  "description": "Milk, eggs, bread",
  "priority":    "High",
  "due_date":    "2026-12-31"
}
```

Response `201`:
```json
{ "success": true, "data": { "id": 1, "status": "Pending", ... } }
```

Validation errors return `400`:
```json
{ "success": false, "error": "Task title is required and cannot be empty." }
```

---

### PUT /api/tasks/{id}
Update an existing task (all fields optional).

Request body:
```json
{
  "title":    "Updated title",
  "priority": "Low",
  "status":   "Completed"
}
```

Response `200` or `404`.

---

### PATCH /api/tasks/{id}/complete
Mark a task as Completed.

Response `200`:
```json
{ "success": true, "data": { "id": 1, "status": "Completed", ... } }
```

---

### DELETE /api/tasks/{id}
Permanently delete a task.

Response `200`:
```json
{ "success": true, "data": { "message": "Task 1 deleted successfully." } }
```

---

## 🔬 Manual Testing with Postman

1. Download and open **Postman** (https://www.postman.com/downloads/).
2. Create a new Collection called "Task Manager".
3. Add requests for each endpoint listed above.
4. Set the **base URL** to `http://127.0.0.1:5000`.
5. For POST and PUT requests:
   - Set **Body** → **raw** → **JSON**.
   - Paste the example JSON from above.
6. Send and inspect the response.

---

## 🗄 Database Schema

```sql
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT,
    priority    TEXT    NOT NULL DEFAULT 'Medium',
    due_date    TEXT,
    status      TEXT    NOT NULL DEFAULT 'Pending',
    created_at  TEXT    NOT NULL
);
```

All queries use parameterised placeholders (`?`) to prevent SQL injection.

---

## 🐙 Git & GitHub Setup

```powershell
# Initialise a local repository
git init
git add .
git commit -m "Initial commit: Task Management System"

# Connect to GitHub (replace <username> and <repo>)
git remote add origin https://github.com/<username>/task-management-system.git
git branch -M main
git push -u origin main
```

---

## 📄 Portfolio Description

> **Task Management System** — Python / Flask / SQLite / HTML / CSS / JavaScript
>
> Built a full-stack, responsive web application from scratch allowing users to create, view, edit, complete, and delete tasks. The backend exposes a RESTful JSON API built with Python and Flask, backed by a parameterised SQLite database to prevent SQL injection. The frontend is written in plain HTML5, CSS3, and vanilla JavaScript using the Fetch API — no frontend frameworks. Includes automated unit tests built with Python's `unittest` framework and an in-memory test database to ensure test isolation. Demonstrates skills in REST API design, SQL database management, server-side validation, client-side DOM manipulation, responsive web design, and professional project organisation.

---

## 🛠 Technology Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python 3.10+, Flask 3 |
| Database   | SQLite (via `sqlite3` stdlib module) |
| Frontend   | HTML5, CSS3, Vanilla JavaScript (ES2021) |
| Testing    | Python `unittest` |
| Dev server | Flask built-in (debug mode) |
