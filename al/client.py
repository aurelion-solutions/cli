import httpx

from al.config import DEFAULT_HTTP_TIMEOUT


class APIClient:
    def __init__(self, base_url: str):
        self.client = httpx.Client(base_url=base_url, timeout=DEFAULT_HTTP_TIMEOUT)

    def get(self, path: str):
        r = self.client.get(path)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, data: dict):
        r = self.client.post(path, json=data)
        r.raise_for_status()
        return r.json()
