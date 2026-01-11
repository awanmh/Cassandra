import logging
import re
import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
from core.database import SessionLocal, FoundSecret, FoundEndpoint
from core.notifier import send_discord_alert

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Regex Patterns for Secrets
SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
    "Stripe Publishable Key": r"pk_live_[0-9a-zA-Z]{24}",
    "Generic Private Key": r"-----BEGIN PRIVATE KEY-----",
    "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})"
}

# Regex for Endpoints
# Matches /api/v1/..., /v1/..., /admin/..., /internal/...
# Starts with slash, followed by specific keywords, then path chars
ENDPOINT_PATTERN = r"[\'\"](\/(?:api\/v\d+|v\d+|admin|internal|private)\/[a-zA-Z0-9\/_\-]+)[\'\"]"

class JSSecretScanner:
    def __init__(self):
        pass

    async def scan(self, url: str):
        """
        Scans all JS files loaded by the URL for secrets and endpoints.
        """
        logger.info(f"Starting JS Scan for {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            js_urls = set()

            page.on("request", lambda request: js_urls.add(request.url) if request.resource_type == "script" else None)

            try:
                await page.goto(url, timeout=30000, wait_until="networkidle")
            except Exception as e:
                logger.error(f"Failed to load page {url}: {e}")
                await browser.close()
                return

            logger.info(f"Found {len(js_urls)} JS files.")

            for js_link in js_urls:
                try:
                    response = await page.request.get(js_link)
                    if response.status == 200:
                        content = await response.text()
                        self._analyze_content(content, js_link, url)
                except Exception as e:
                    logger.warning(f"Failed to fetch JS {js_link}: {e}")

            await browser.close()

    def _analyze_content(self, content: str, source_url: str, target_url: str):
        """
        Regex match content for secrets and endpoints.
        """
        db = SessionLocal()
        try:
            # 1. Search Secrets
            for secret_name, pattern in SECRET_PATTERNS.items():
                matches = re.findall(pattern, content)
                for match in matches:
                    logger.warning(f"POTENTIAL SECRET FOUND: {secret_name} in {source_url}")
                    
                    exists = db.query(FoundSecret).filter_by(value=match, target=target_url).first()
                    if not exists:
                        secret = FoundSecret(target=target_url, secret_type=secret_name, value=match, file_source=source_url)
                        db.add(secret)
                        db.commit()
                        send_discord_alert("Secret Found!", f"Type: {secret_name}\nTarget: {target_url}\nValue: {match}", "HIGH")

            # 2. Search Endpoints
            matches = re.findall(ENDPOINT_PATTERN, content)
            if matches:
                 unique_endpoints = set(matches)
                 logger.info(f"Found {len(unique_endpoints)} endpoints in {source_url}")
                 
                 for ep in unique_endpoints:
                     exists = db.query(FoundEndpoint).filter_by(endpoint=ep, target=target_url).first()
                     if not exists:
                         endpoint_rec = FoundEndpoint(target=target_url, endpoint=ep, source_url=source_url)
                         db.add(endpoint_rec)
                 db.commit()

        except Exception as e:
            logger.error(f"DB Error: {e}")
        finally:
            db.close()

def run_scan(url: str):
    scanner = JSSecretScanner()
    asyncio.run(scanner.scan(url))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    
    run_scan(args.target)
