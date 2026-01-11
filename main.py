import argparse
import sys
import json
import logging
import subprocess
import os
from pathlib import Path
from colorama import Fore, Style, init

# Init modules
from config.settings import settings
from core.scope_parser import scope_parser
from core.auth_manager import auth_manager
from core.notifier import send_alert

# Modules
from modules.sqli_runner import sqli_runner
from modules.xss_runner import xss_runner
from modules.idor_hunter import idor_hunter
from modules.secret_hunter import secret_hunter

init(autoreset=True)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.CYAN}[%(asctime)s] {Style.RESET_ALL}%(message)s",
    datefmt="%H:%M:%S"
)

# Debug Environment
print(f"DEBUG: Loaded Webhook URL: {os.getenv('DISCORD_WEBHOOK_URL')}")

def main():
    parser = argparse.ArgumentParser(description="Cassandra Ultimate - Autonomous Security Agent")
    parser.add_argument("--target", help="Single target domain (optional override)")
    parser.add_argument("--policy", help="Path to policy text file", required=True)
    parser.add_argument("--mode", choices=["recon", "attack", "full"], default="recon", help="Scan mode")
    parser.add_argument("--login", action="store_true", help="Perform authentication")
    
    args = parser.parse_args()

    # 1. Parse Scope
    logging.info("Step 1: Parsing Scope...")
    with open(args.policy, "r") as f:
        policy_text = f.read()
    
    target_config = scope_parser.parse(policy_text)
    
    if not target_config.in_scope_domains:
        logging.error("No in-scope domains found!")
        sys.exit(1)
        
    logging.info(f"In-Scope: {target_config.in_scope_domains}")
    logging.info(f"Out-Of-Scope: {target_config.out_of_scope_domains}")

    # Prepare Config for Go Scanner
    go_config = {
        "in_scope_domains": target_config.in_scope_domains,
        "out_of_scope_domains": target_config.out_of_scope_domains,
        "output_dir": str(settings.DATA_DIR)
    }
    
    config_path = settings.DATA_DIR / "scan_config.json"
    with open(config_path, "w") as f:
        json.dump(go_config, f)

    # 2. Go Recon (Subfinder + Filtering + Nuclei)
    logging.info("Step 2: Launching Go Scanner (Recon)...")
    
    # We must compile or run the go code. 
    # Check if 'go' is installed and run 'go run' or build it.
    # To be robust, let's try 'go run scanner/main.go --config ...' relative to root
    
    scanner_dir = Path("scanner")
    if not scanner_dir.exists():
        logging.error("Scanner directory not found!")
        sys.exit(1)
        
    # go run . would look for package main in current dir (scanner/)
    # Config path must be absolute or relative to scanner/
    # Let's make it absolute for safety
    abs_config_path = config_path.resolve()
    
    cmd = ["go", "run", ".", "--config", str(abs_config_path)]
    
    # PATH Fix: Ensure Go bin is in PATH
    go_path = Path.home() / "go" / "bin"
    env = os.environ.copy()
    if go_path.exists():
        env["PATH"] = str(go_path) + os.pathsep + env["PATH"]
        logging.info(f"Added {go_path} to PATH")

    try:
        logging.info(f"Running Go Scanner in {scanner_dir.resolve()}...")
        subprocess.run(cmd, cwd=scanner_dir, check=True, env=env)
    except subprocess.CalledProcessError:
        logging.error("Go scanner failed.")
        sys.exit(1)

    if args.mode == "recon":
        logging.info("Recon complete. Check data/ folder.")
        return

    # 3. Authentication (Optional)
    if args.login:
        logging.info("Step 3: Authenticating...")
        # Pick the first in-scope domain or the main one
        target_url = f"https://{target_config.in_scope_domains[0]}"
        auth_manager.login(target_url)

    # 4. Active Attacks
    if args.mode in ["attack", "full"]:
        logging.info("Step 4: Launching Attack Modules...")
        
        # Load subdomains found by Go scanner
        # Load alive domains (filtered by httpx)
        subs_file = settings.DATA_DIR / "alive.txt"
        if not subs_file.exists():
            # Fallback to subdomains.txt if alive.txt doesn't exist (e.g. httpx failed)
             subs_file = settings.DATA_DIR / "subdomains.txt"
             
        if not subs_file.exists():
            logging.warning("No subdomains file found. Skipping attacks.")
            return
            
        logging.info(f"Loading targets from {subs_file}...")
        with open(subs_file, "r") as f:
            subdomains = f.read().splitlines()

        for sub in subdomains:
            if sub.startswith("http://") or sub.startswith("https://"):
                url = sub
            else:
                url = f"https://{sub}" # Assume HTTPS if missing
            
            logging.info(f"Attacking {url}...")
            
            # Run modules
            # 1. SQLi
            sqli_runner.scan(url)
            
            # 2. XSS
            xss_runner.scan(url)
            
            # 3. IDOR (Need endpoints with IDs, usually we crawl first, but here we just test root or known paths if crawling was better)
            # The current IDOR hunter expects a full URL with path.
            # Realistically we need a crawler output. RunNuclei might have found active URLs.
            # Let's check if Nuclei results exist and use them.
            nuclei_file = settings.DATA_DIR / "nuclei_results.txt"
            if nuclei_file.exists():
                 with open(nuclei_file, "r") as nf:
                     for line in nf:
                         # Nuclei output format varies, usually [template-id] [protocol] [severity] URL
                         # If -silent, it might just be the URL or formatted.
                         # The Runner uses -silent. Nuclei default silent is just URL if it matched? 
                         # Actually Nuclei silent output is usually `[id] url`.
                         parts = line.split()
                         if len(parts) > 1:
                             found_url = parts[-1] 
                             if found_url.startswith("http"):
                                 idor_hunter.scan(found_url)
                                 secret_hunter.scan_js(found_url) # Scan if it's JS? Or scan page content.

            # Also scan the root
            secret_hunter.scan_js(url) # This expects JS url, need to crawl for JS.

    logging.info("Mission Complete.")
    send_alert("Scan Finished", "Status", "Cassandra has finished the mission.", "INFO")

if __name__ == "__main__":
    main()
