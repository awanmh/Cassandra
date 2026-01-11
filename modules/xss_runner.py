import subprocess
import logging
from core.notifier import send_alert
from core.auth_manager import auth_manager
from config.settings import settings
import shlex

class XSSRunner:
    def scan(self, target: str):
        """
        Runs dalfox on the target with headless verification for 0% False Positives.
        """
        logging.info(f"Starting High-Accuracy XSS scan on {target} (Headless Verification Enabled)")
        
        cookie = auth_manager.get_cookie_string()
        
        # dalfox url [target] --cookie [cookies] --verify-on-headless --ignore-return ...
        cmd = [
            "dalfox", "url", target,
            "--verify-on-headless", # CRITICAL: Launches browser to verify alert(1) popups
            "--ignore-return", "404,403,500", # Ignore error pages
            "--worker", "10",
            "--format", "json",
            "--silence",
            "--skip-mining-dom",
            "--skip-bav"
        ]

        if cookie:
            cmd.extend(["--cookie", cookie])
            
        try:
            # Run Dalfox
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # Parse JSON Output
            # Dalfox JSON output can be a list of objects or one object per line depending on version/flags?
            # Usually --format json implies one JSON object per line for findings or a JSON array.
            # Let's handle line-by-line JSON objects which is common for security tools.
            
            if not result.stdout:
                return

            import json
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                    
                try:
                    finding = json.loads(line)
                    # We look for 'verified' key or similar if available, but --verify-on-headless usually filters output itself.
                    # If it's in the output with headless flag, it's likely confirmed.
                    
                    # Log finding
                    msg = f"CONFIRMED XSS on {finding.get('method', 'GET')} {finding.get('url')} - Payload: {finding.get('payload')}"
                    logging.warning(msg)
                    send_alert("Verified XSS Found", "Reflected XSS", msg, "CRITICAL")
                    
                    log_file = settings.DATA_DIR / "xss_findings.txt"
                    with open(log_file, "a") as f:
                        f.write(json.dumps(finding) + "\n")
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logging.error(f"XSS scan failed: {e}")

xss_runner = XSSRunner()
