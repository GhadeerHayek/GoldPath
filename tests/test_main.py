import unittest

from fastapi.testclient import TestClient

from app.main import app


class DemoTest(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = TestClient(self.app)

    def test_health(self):
        response = self.client.get("/health")
        status = response.json().get("status")
        self.assertEqual(status, "ok")
