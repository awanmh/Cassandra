import argparse
import sys
import os
import logging
from pathlib import Path
from colorama import Fore, Style, init

# Init modules
from config.settings import settings
from core.scope_parser import scope_parser
from core.auth_manager import auth_manager
from core.notifier import send_alert
from core.orchestrator import SmartOrchestrator
from core.database import init_db

init(autoreset=True)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.CYAN}[%(asctime)s] {Style.RESET_ALL}%(message)s",
    datefmt="%H:%M:%S"
)

def main():
    parser = argparse.ArgumentParser(description="Cassandra Ultimate 2.0 - Smart Reconnaissance Weapon")
    parser.add_argument("--target", help="Single target domain (optional override)")
    parser.add_argument("--policy", help="Path to policy text file", required=True)
    parser.add_argument("--mode", choices=["recon", "attack", "full"], default="recon", help="Scan mode")
    parser.add_argument("--login", action="store_true", help="Perform authentication")
    
    args = parser.parse_args()

    # Initialize Database
    init_db()

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

    # 2. Go Recon (Subsystem)
    # Kept for initial subdomain discovery which populates 'alive.txt' or similar
    # The original logic for calling Go scanner is preserved but we might want to ensure it runs correctly
    # For now, let's assume the user runs the original Go scanner Logic OR we integrate it here.
    # To keep 2.0 focused on "Smart Orchestration", we invoke the Go scanner as a step before smart analysis.
    
    if args.mode in ["recon", "full"]:
        logging.info("Step 2: Launching Go Scanner (Network Recon)...")
        # Reuse existing Go scanner invocation logic
        _run_go_scanner(target_config)

    # 3. Smart Orchestration (The Brain)
    if args.mode in ["attack", "full"]:
        logging.info("Step 3: Engaging Smart Orchestration...")
        
        # Load targets (prefer alive.txt from Go scanner, else scope)
        targets = []
        alive_file = settings.DATA_DIR / "alive.txt"
        
        if alive_file.exists():
            with open(alive_file, "r") as f:
                targets = [line.strip() for line in f if line.strip()]
        else:
            targets = target_config.in_scope_domains
            
        orchestrator = SmartOrchestrator(targets)
        orchestrator.run()
        orchestrator.cleanup()

    logging.info("Mission Complete.")
    send_alert("Scan Finished", "Status", "Cassandra 2.0 has finished the mission.", "INFO")

def _run_go_scanner(target_config):
    """Helper to run the Go-based scanner component"""
    config_path = settings.DATA_DIR / "scan_config.json"
    go_config = {
        "in_scope_domains": target_config.in_scope_domains,
        "out_of_scope_domains": target_config.out_of_scope_domains,
        "output_dir": str(settings.DATA_DIR)
    }
    
    with open(config_path, "w") as f:
        import json
        json.dump(go_config, f)
        
    scanner_dir = Path("scanner")
    if not scanner_dir.exists():
        logging.warning("Scanner directory not found, skipping Go recon.")
        return

    # Check for go
    import shutil
    if not shutil.which("go"):
         logging.warning("Go not found in PATH. Skipping Go scanner.")
         return

    cmd = ["go", "run", ".", "--config", str(config_path.resolve())]
    
    try:
        subprocess.run(cmd, cwd=scanner_dir, check=False)
    except Exception as e:
        logging.error(f"Go scanner error: {e}")

if __name__ == "__main__":
    main()
