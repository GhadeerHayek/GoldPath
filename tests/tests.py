import unittest
import requests


BASE_URL = "http://0.0.0.0:8000"

class DemoTest(unittest.TestCase):
    def test_health(self):
        response = requests.get(f"{BASE_URL}/health")
        status = response.json().get("status")
        self.assertEqual(status, "ok")
