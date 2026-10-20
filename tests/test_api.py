"""
tests/test_api.py
------------------
Automated tests for the Task Management System REST API.

Covers:
  1.  Creating a task successfully
  2.  Retrieving all tasks
  3.  Retrieving a task by ID
  4.  Updating a task
  5.  Completing a task
  6.  Deleting a task
  7.  Submitting invalid input (missing title, bad priority)
  8.  Requesting a task that does not exist (404)

A temporary SQLite file is used for the test database.  SQLite in-memory
databases (":memory:") are connection-scoped — every new sqlite3.connect()
call produces a separate, empty database — so they cannot be shared
between the Flask test client's request-handling connections and the test
setup helpers.  A named temp file avoids this problem entirely.

Run with:
    python -m unittest tests/test_api.py -v
"""

import sys
import os
import json
import tempfile
import unittest

# Put the project root on the path so we can import app.py and database.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database  # imported before app so the monkey-patch takes effect first
from database import init_db


class TestTaskAPI(unittest.TestCase):
    """End-to-end tests for all REST API endpoints."""

    @classmethod
    def setUpClass(cls):
        """
        Runs once before the whole test class.
        Create a temporary file to use as the test database, then initialise
        the schema so the 'tasks' table exists before any request is made.
        """
        # mkstemp returns an open file descriptor + path; close the fd immediately
        fd, cls.db_path = tempfile.mkstemp(suffix=".db", prefix="test_tasks_")
        os.close(fd)

        # Redirect the database module to use our temp file
        database.DB_PATH = cls.db_path

        # Create the tasks table
        init_db(cls.db_path)

        # Import and configure the Flask app *after* patching DB_PATH
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        cls.flask_app = flask_app

    @classmethod
    def tearDownClass(cls):
        """Remove the temp database file after all tests finish."""
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def setUp(self):
        """Create a fresh test client before each individual test."""
        self.client = self.flask_app.test_client()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def post_task(self, title="Test Task", description="Desc",
                  priority="Medium", due_date=None):
        """POST to /api/tasks and return the Response object."""
        payload = {"title": title, "description": description, "priority": priority}
        if due_date:
            payload["due_date"] = due_date
        return self.client.post(
            "/api/tasks",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def parse(self, response):
        """Decode a Flask Response to a Python dict."""
        return json.loads(response.data)

    # ------------------------------------------------------------------
    # Test 1: Create a task successfully → 201
    # ------------------------------------------------------------------

    def test_01_create_task_success(self):
        res  = self.post_task(title="Buy groceries", priority="High",
                              due_date="2026-12-31")
        body = self.parse(res)

        self.assertEqual(res.status_code, 201, msg=body)
        self.assertTrue(body["success"])
        task = body["data"]
        self.assertEqual(task["title"],    "Buy groceries")
        self.assertEqual(task["priority"], "High")
        self.assertEqual(task["status"],   "Pending")
        self.assertIn("id", task)
        self.assertIn("created_at", task)

    # ------------------------------------------------------------------
    # Test 2: Retrieve all tasks → 200 with a list
    # ------------------------------------------------------------------

    def test_02_get_all_tasks(self):
        self.post_task(title="Task Alpha")
        self.post_task(title="Task Beta")

        res  = self.client.get("/api/tasks")
        body = self.parse(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(body["success"])
        tasks = body["data"]["tasks"]
        self.assertIsInstance(tasks, list)
        self.assertGreaterEqual(len(tasks), 2)

    # ------------------------------------------------------------------
    # Test 3: Retrieve a task by ID → 200 with correct data
    # ------------------------------------------------------------------

    def test_03_get_task_by_id(self):
        create_res = self.post_task(title="Unique Task XYZ", priority="Low")
        task_id    = self.parse(create_res)["data"]["id"]

        res  = self.client.get(f"/api/tasks/{task_id}")
        body = self.parse(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["id"],    task_id)
        self.assertEqual(body["data"]["title"], "Unique Task XYZ")

    # ------------------------------------------------------------------
    # Test 4: Update a task → 200 with updated fields
    # ------------------------------------------------------------------

    def test_04_update_task(self):
        task_id = self.parse(self.post_task(title="Old Title", priority="Low"))["data"]["id"]

        res  = self.client.put(
            f"/api/tasks/{task_id}",
            data=json.dumps({"title": "New Title", "priority": "High",
                             "description": "Updated description"}),
            content_type="application/json",
        )
        body = self.parse(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["title"],    "New Title")
        self.assertEqual(body["data"]["priority"], "High")

    # ------------------------------------------------------------------
    # Test 5: Complete a task → 200, status becomes "Completed"
    # ------------------------------------------------------------------

    def test_05_complete_task(self):
        task_id = self.parse(self.post_task(title="Task to Complete"))["data"]["id"]

        res  = self.client.patch(f"/api/tasks/{task_id}/complete")
        body = self.parse(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["status"], "Completed")

    # ------------------------------------------------------------------
    # Test 6: Delete a task → 200, then 404 on second attempt
    # ------------------------------------------------------------------

    def test_06_delete_task(self):
        task_id = self.parse(self.post_task(title="Task to Delete"))["data"]["id"]

        # First delete succeeds
        res  = self.client.delete(f"/api/tasks/{task_id}")
        body = self.parse(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(body["success"])

        # Second delete → 404
        res2  = self.client.delete(f"/api/tasks/{task_id}")
        body2 = self.parse(res2)
        self.assertEqual(res2.status_code, 404)
        self.assertFalse(body2["success"])

    # ------------------------------------------------------------------
    # Test 7a: Invalid input — empty title → 400
    # ------------------------------------------------------------------

    def test_07a_invalid_empty_title(self):
        res  = self.post_task(title="", priority="Medium")
        body = self.parse(res)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(body["success"])
        self.assertIn("title", body["error"].lower())

    # ------------------------------------------------------------------
    # Test 7b: Invalid input — bad priority → 400
    # ------------------------------------------------------------------

    def test_07b_invalid_priority(self):
        payload = {"title": "Valid Title", "priority": "Extreme"}
        res  = self.client.post("/api/tasks", data=json.dumps(payload),
                                content_type="application/json")
        body = self.parse(res)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(body["success"])
        self.assertIn("priority", body["error"].lower())

    # ------------------------------------------------------------------
    # Test 7c: Invalid input — no JSON body → 400
    # ------------------------------------------------------------------

    def test_07c_missing_body(self):
        res  = self.client.post("/api/tasks", data="not-json",
                                content_type="text/plain")
        body = self.parse(res)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(body["success"])

    # ------------------------------------------------------------------
    # Test 8: Non-existent task ID → 404
    # ------------------------------------------------------------------

    def test_08_task_not_found(self):
        res  = self.client.get("/api/tasks/999999")
        body = self.parse(res)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(body["success"])
        self.assertIn("not found", body["error"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
