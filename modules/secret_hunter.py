import re
import requests # Added missing import
import logging
from core.waf_evader import waf_evader
from core.notifier import send_alert
from config.settings import settings

class SecretHunter:
    def scan_js(self, js_url: str):
        """
        Downloads JS file and scans for secrets using Regex.
        """
        try:
            resp = waf_evader.get(js_url)
            if resp.status_code != 200:
                return

            content = resp.text
            self._analyze_content(js_url, content)
            
        except requests.exceptions.ConnectionError:
            print(f"[-] Target dead/unreachable: {js_url}") # Use print or logging as preferred, logging is setup
            logging.warning(f"[-] Target dead/unreachable: {js_url}")
        except Exception as e:
            logging.error(f"Secret scan failed for {js_url}: {e}")

    def _analyze_content(self, url, content):
        patterns = {
            "AWS Key": r"AKIA[0-9A-Z]{16}",
            "Google API": r"AIza[0-9A-Za-z\\-_]{35}",
            "Generic Bearer": r"Bearer [a-zA-Z0-9\\-\\_\\.]+",
            "Private Key": r"-----BEGIN PRIVATE KEY-----"
        }

        for name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                msg = f"Found {name} in {url}: {match[:10]}..." # Truncate for safety
                logging.warning(msg)
                send_alert(f"{name} Leaked", "Secret Leak", msg, "HIGH")
                
                with open(settings.DATA_DIR / "secrets.txt", "a") as f:
                    f.write(f"[{name}] {url} -> {match}\n")

secret_hunter = SecretHunter()
