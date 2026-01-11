import requests
import random
import time
from fake_useragent import UserAgent
from core.auth_manager import auth_manager

class WAFEvader:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()

    def get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "X-Forwarded-For": "127.0.0.1",
            "X-Originating-IP": "127.0.0.1",
            "Cookie": auth_manager.get_cookie_string()
        }

    def get(self, url, **kwargs):
        time.sleep(random.uniform(0.5, 2.0))
        kwargs.setdefault("headers", {}).update(self.get_headers())
        return self.session.get(url, **kwargs)

    def post(self, url, **kwargs):
        time.sleep(random.uniform(0.5, 2.0))
        kwargs.setdefault("headers", {}).update(self.get_headers())
        return self.session.post(url, **kwargs)

waf_evader = WAFEvader()
