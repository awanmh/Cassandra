import requests
import re
import difflib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from core.waf_evader import waf_evader
from core.notifier import send_alert
import logging

class IDORHunter:
    def scan(self, url: str):
        """
        Detects numeric IDs in URL, rotates them, and compares responses.
        """
        parsed = urlparse(url)
        path_segments = parsed.path.split('/')
        
        # Check path for numeric IDs
        for i, segment in enumerate(path_segments):
            if segment.isdigit():
                original_id = int(segment)
                self._test_idor(url, i, original_id, is_path=True)

        # Check query params
        params = parse_qs(parsed.query)
        for key, values in params.items():
            for val in values:
                if val.isdigit():
                    self._test_idor(url, key, int(val), is_path=False)

    def _test_idor(self, url, target_key, original_id, is_path=False):
        # Baseline request
        try:
            r_base = waf_evader.get(url)
            if r_base.status_code != 200:
                return

            # Attack request (original_id + 1)
            attack_id = original_id + 1
            if is_path:
                parsed = urlparse(url)
                segments = parsed.path.split('/')
                segments[target_key] = str(attack_id)
                new_path = "/".join(segments)
                attack_url = parsed._replace(path=new_path).geturl()
            else:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                params[target_key] = [str(attack_id)]
                new_query = urlencode(params, doseq=True)
                attack_url = parsed._replace(query=new_query).geturl()

            r_attack = waf_evader.get(attack_url)
            
            # Compare responses
            diff = difflib.SequenceMatcher(None, r_base.text, r_attack.text).ratio()
            
            # Heuristic: High similarity (but not identical) + Success Code might indicate IDOR
            # User Preference: 0.90 < similarity < 1.0
            if r_attack.status_code == 200 and 0.90 < diff < 1.0:
                 msg = f"🔥 POTENSI IDOR! {url} -> {attack_url} (Similarity: {diff:.2f})"
                 logging.warning(msg)
                 send_alert("Potential IDOR Found", "IDOR", msg, "HIGH")

        except requests.exceptions.ConnectionError:
            logging.warning(f"[-] Target dead/unreachable: {url}")
        except Exception as e:
            logging.error(f"IDOR scan failed: {e}")

idor_hunter = IDORHunter()
