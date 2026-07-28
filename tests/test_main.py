import unittest

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
