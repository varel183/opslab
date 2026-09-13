import os
import shutil
import tempfile
import unittest

temp_directory = tempfile.mkdtemp()
temp_database = os.path.join(temp_directory, "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{temp_database}"

from fastapi.testclient import TestClient

from app.database import engine
from app.main import app


class TaskApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        engine.dispose()
        shutil.rmtree(temp_directory)

    def test_health_and_readiness(self) -> None:
        self.assertEqual(self.client.get("/health").json(), {"status": "healthy"})
        self.assertEqual(self.client.get("/ready").status_code, 200)

    def test_task_lifecycle(self) -> None:
        created = self.client.post(
            "/tasks", json={"title": "Learn Docker", "description": "Build an image"}
        )
        self.assertEqual(created.status_code, 201)
        task_id = created.json()["id"]

        updated = self.client.patch(f"/tasks/{task_id}", json={"status": "done"})
        self.assertEqual(updated.json()["status"], "done")

        listed = self.client.get("/tasks")
        self.assertTrue(any(task["id"] == task_id for task in listed.json()))

        deleted = self.client.delete(f"/tasks/{task_id}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get(f"/tasks/{task_id}").status_code, 404)

    def test_rejects_invalid_status(self) -> None:
        response = self.client.post("/tasks", json={"title": "Bad task", "status": "unknown"})
        self.assertEqual(response.status_code, 422)

    def test_observability_demo_endpoints(self) -> None:
        slow = self.client.get("/demo/slow?delay_ms=1")
        self.assertEqual(slow.status_code, 200)
        self.assertEqual(slow.json()["delay_ms"], 1)

        error = self.client.get("/demo/error")
        self.assertEqual(error.status_code, 500)
        self.assertIn("Intentional error", error.json()["detail"])


if __name__ == "__main__":
    unittest.main()
