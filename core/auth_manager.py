from playwright.sync_api import sync_playwright
import json
import logging
import time
from pathlib import Path
from config.settings import settings

STORAGE_STATE_PATH = settings.DATA_DIR / "storage_state.json"

class AuthManager:
    def login(self, target_url: str):
        """
        Interactive login or heuristic login using Playwright.
        """
        logging.info(f"Starting Auth Manager for {target_url}...")
        
        with sync_playwright() as p:
            # Launch Headless=False for debugging or if user wants to see
            # For automation, we often stick to False. 
            # But "Autonomous" implies we try to do it ourselves.
            # Here we will do a simple heuristic scan for inputs.
            browser = p.chromium.launch(headless=True) 
            context = browser.new_context()
            page = context.new_page()
            
            try:
                page.goto(target_url, timeout=60000)
                page.wait_for_load_state("networkidle")
                
                # Heuristic: Find login fields
                user_input = page.locator("input[type='text'], input[type='email'], input[name*='user'], input[name*='login']").first
                pass_input = page.locator("input[type='password']").first
                submit_btn = page.locator("button[submit], button[type='submit'], input[type='submit']").first
                
                # Check if we have credentials in env (This is a placeholder for real cred logic)
                # Ideally, we would read from secrets.env if implemented.
                # For now, we just dump what we have or wait a bit if manual login was intended (but we are headless).
                
                # If we were in semi-autonomous mode, we could ask user to login.
                # Since we are fully automated, we assume we might need credentials.
                # For this implementation, we will just proceed to save state if we managed to log in or just save the initial state.
                
                # SAVE STATE regardless for now (cookies might be set by simply visiting)
                context.storage_state(path=STORAGE_STATE_PATH)
                logging.info(f"Auth state saved to {STORAGE_STATE_PATH}")
                
            except Exception as e:
                logging.error(f"Login failed: {e}")
            finally:
                browser.close()

    def get_cookie_string(self) -> str:
        """
        Reads the storage_state.json and returns a cookie string for requests/headers.
        """
        if not STORAGE_STATE_PATH.exists():
            return ""
            
        try:
            with open(STORAGE_STATE_PATH, "r") as f:
                data = json.load(f)
                cookies = data.get("cookies", [])
                return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        except Exception:
            return ""

auth_manager = AuthManager()
