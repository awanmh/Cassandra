import logging
import json
import subprocess
import time
import random
import itertools
from pathlib import Path
from typing import List, Dict

from core.database import SessionLocal, ScanResult
from core.notifier import send_discord_alert
from modules.fingerprint import TechFingerprinter
from modules.js_scanner import run_scan as run_js_scan
from config.settings import settings

# Setup Logging
logger = logging.getLogger(__name__)

class SmartOrchestrator:
    def __init__(self, target_domains: List[str]):
        self.targets = target_domains
        self.fingerprinter = TechFingerprinter()
        self.tech_rules = self._load_rules()
        self.proxies = self._load_proxies()
        self.deny_list = self._load_deny_list()
        self.proxy_cycle = itertools.cycle(self.proxies) if self.proxies else None
        self.db = SessionLocal()

    def _load_rules(self) -> Dict:
        """Load tech rules from JSON config."""
        rules_path = Path("config/tech_rules.json")
        if rules_path.exists():
            with open(rules_path, "r") as f:
                return json.load(f)
        return {}

    def _load_proxies(self) -> List[str]:
        """Load proxies from file."""
        proxy_path = Path("config/proxies.txt")
        proxies = []
        if proxy_path.exists():
            with open(proxy_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxies.append(line)
        logger.info(f"Loaded {len(proxies)} proxies.")
        return proxies

    def _load_deny_list(self) -> List[str]:
        """Load out-of-scope domains."""
        deny_path = Path("config/scope_deny.txt")
        deny_list = []
        if deny_path.exists():
            with open(deny_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deny_list.append(line)
        return deny_list

    def _get_next_proxy(self):
        """Get next proxy from rotation."""
        if self.proxy_cycle:
            return next(self.proxy_cycle)
        return None

    def _is_safe_target(self, target: str) -> bool:
        """Check if target is in deny list."""
        for denied in self.deny_list:
            if denied in target:
                logger.warning(f"🚫 SKIPPING {target}: Matches deny list pattern '{denied}'")
                return False
        return True

    def run(self):
        """
        Main execution flow:
        1. Recon (via generic or existing scope)
        2. Fingerprint
        3. Smart Decision
        4. Attack Execution
        """
        logger.info("Initializing Smart Orchestration v2.1...")
        
        for target in self.targets:
            # Scope Safety Check
            if not self._is_safe_target(target):
                continue

            # Normalize URL
            if not target.startswith("http"):
                url = f"https://{target}"
            else:
                url = target

            logger.info(f"Processing Target: {url}")

            # Step 1: Tech Fingerprinting (The Eyes)
            # Pass proxy if needed (Function signature update required if we want to proxy this too)
            # For now, let's assume fingerprinting uses system proxy or direct connection for speed
            # unless strictly required.
            tech_profile = self.fingerprinter.identify_tech(url)
            self._save_scan_result(url, "Fingerprint", "INFO", tech_profile)
            
            logger.info(f"Identified Tech: {tech_profile['all']}")

            # Step 2: Decision Engine & Execution (The Brain)
            self._execute_smart_attacks(url, tech_profile)

            # Step 3: Always run JS Scanner (The Looter)
            logger.info("Running JS Secret Scanner...")
            run_js_scan(url)

    def _execute_smart_attacks(self, url: str, tech_profile: Dict):
        """
        Match found technologies against rules and trigger commands.
        """
        all_techs = tech_profile.get('all', [])
        triggered_rules = set()

        # Build Proxy Flag
        proxy = self._get_next_proxy()
        proxy_flag = f" -proxy {proxy}" if proxy else ""

        for tech in all_techs:
            for rule_name, rule_data in self.tech_rules.items():
                if rule_name.lower() == tech.lower():
                    if rule_name not in triggered_rules:
                        logger.info(f"[+] Tech Match: {rule_name}! Triggering specific attacks.")
                        triggered_rules.add(rule_name)
                        
                        # Execute Commands
                        for cmd_template in rule_data.get("commands", []):
                            # Append proxy if external tool
                            cmd = cmd_template.format(target=url)
                            
                            # Naive check for tool support (Nuclei, Dalfox supports -proxy)
                            # WPScan supports --proxy
                            # If it's a python module run, we skip adding flags unless passed as arg
                            if "nuclei" in cmd and proxy:
                                cmd += proxy_flag
                            elif "wpscan" in cmd and proxy:
                                cmd += f" --proxy {proxy}"
                            elif "dalfox" in cmd and proxy:
                                cmd += f" --proxy {proxy}"
                            
                            self._run_safe_command(cmd)

        if not triggered_rules:
            logger.info("No specific tech rules matched. Running generic fallbacks.")
            cmd = f"nuclei -u {url} -silent"
            if proxy:
                cmd += proxy_flag
            self._run_safe_command(cmd)

    def _run_safe_command(self, cmd_str: str):
        """
        Run command with error handling, smart delays, and proxy rotation.
        """
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            try:
                logger.info(f"Executing: {cmd_str}")
                # Real-time alert for start (optional, maybe too noisy)
                
                start_time = time.time()
                result = subprocess.run(cmd_str, shell=True, check=False, capture_output=True, text=True)
                duration = time.time() - start_time

                if result.returncode == 0:
                    # Success
                    self._parse_and_alert(cmd_str, result.stdout)
                    return
                else:
                    # Check for rate limiting
                    if "429" in result.stderr or "Too Many Requests" in result.stderr:
                        wait_time = random.randint(30, 60)
                        logger.warning(f"⚠️ Rate Limited (429). Sleeping for {wait_time}s...")
                        time.sleep(wait_time)
                        
                        # Rotate proxy if possible
                        new_proxy = self._get_next_proxy()
                        if new_proxy:
                            # Replace old proxy in string (Simple string replacement hack)
                            # Ideally we handle structure better, but valid for string cmds
                            # Assuming -proxy http://old...
                            # This is complex to replace in raw string. 
                            # Strategy: Just wait and retry for now.
                            pass
                    else:
                        logger.warning(f"Command failed (Attempt {attempt+1}): {result.stderr[:100]}...")
                
            except Exception as e:
                logger.error(f"Execution Error: {e}")
            
            attempt += 1
            time.sleep(5) # Cooldown

    def _parse_and_alert(self, cmd: str, output: str):
        """
        Parse output for Critical/High issues and alert.
        """
        # Very basic parsing for Nuclei JSON or text
        # If nuclei, we check for [critical] or [high]
        if "nuclei" in cmd:
            if "[critical]" in output.lower():
                send_discord_alert("CRITICAL Vulnerability Found!", f"Command: {cmd}\nOutput Snippet:\n{output[:500]}", "CRITICAL")
            elif "[high]" in output.lower():
                 send_discord_alert("HIGH Vulnerability Found!", f"Command: {cmd}\nOutput Snippet:\n{output[:500]}", "HIGH")

    def _save_scan_result(self, target, scan_type, severity, details):
        """Save results to PG database."""
        try:
            result = ScanResult(
                target=target,
                scan_type=scan_type,
                severity=severity,
                details=details
            )
            self.db.add(result)
            self.db.commit()
        except Exception as e:
            logger.error(f"DB Save Error: {e}")

    def cleanup(self):
        self.db.close()
