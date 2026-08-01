import tomllib
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

BASE_URL = "http://0.0.0.0:8000"


class DemoTest(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = TestClient(self.app)

    def test_health(self):
        response = self.client.get(f"{BASE_URL}/health")
        print(response.status_code)
        status = response.json().get("status")
        self.assertEqual(status, "ok")

    def test_version_matches_pyproject(self):
        pyproject_path = (
            Path(__file__).resolve().parent.parent / "pyproject.toml"
        )
        with pyproject_path.open("rb") as f:
            expected_version = tomllib.load(f)["project"]["version"]

        response = self.client.get(f"{BASE_URL}/version")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": expected_version})
