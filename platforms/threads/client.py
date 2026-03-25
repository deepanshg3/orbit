import os
import requests
from configs.settings import settings

class ThreadsClient:
    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(self):
        self.access_token = settings.THREADS_ACCESS_TOKEN

        if not self.access_token:
            raise ValueError("THREADS_ACCESS_TOKEN not found. Run: source ~/.bashrc")

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def post(self, endpoint: str, data: dict):
        url = f"{self.BASE_URL}/{endpoint}"

        response = requests.post(url, json=data, headers=self._get_headers())

        if response.status_code != 200:
            raise Exception(f"Threads API Error: {response.text}")

        return response.json()

    def get(self, endpoint: str, params: dict = None):
        url = f"{self.BASE_URL}/{endpoint}"

        response = requests.get(url, params=params, headers=self._get_headers())

        if response.status_code != 200:
            raise Exception(f"Threads API Error: {response.text}")

        return response.json()