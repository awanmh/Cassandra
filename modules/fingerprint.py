import logging
import json
import shutil
import subprocess
from typing import Dict, List, Any
from Wappalyzer import Wappalyzer, WebPage
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechFingerprinter:
    def __init__(self):
        self.wappalyzer = Wappalyzer.latest()

    def identify_tech(self, url: str) -> Dict[str, List[str]]:
        """
        Identify technologies used by the target URL.
        Returns a structured dictionary of findings.
        """
        results = {
            'framework': [],
            'cms': [],
            'server': [],
            'lang': [],
            'all': []
        }

        try:
            logger.info(f"Fingerprinting {url}...")
            
            # Method 1: Wappalyzer (Python lib)
            try:
                webpage = WebPage.new_from_url(url)
                wappa_results = self.wappalyzer.analyze(webpage)
                results['all'].extend(list(wappa_results))
                logger.info(f"Wappalyzer found: {wappa_results}")
            except Exception as e:
                logger.error(f"Wappalyzer failed: {e}")

            # Method 2: Fallback to httpx (Go tool) if installed
            # Assuming httpx can be used for tech detect via flag -tech-detect if supported 
            # or simply analyzing headers. Standard httpx -tech-detect output is JSON.
            # Note: httpx -tech-detect is built-in in newer projectdiscovery/httpx.
            
            if shutil.which("httpx"):
                try:
                    cmd = ["httpx", "-u", url, "-tech-detect", "-json", "-silent"]
                    process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if process.returncode == 0 and process.stdout:
                        data = json.loads(process.stdout)
                        if "technologies" in data:
                            results['all'].extend(data["technologies"])
                            logger.info(f"httpx found: {data['technologies']}")
                except Exception as e:
                    logger.error(f"httpx tech-detect failed: {e}")

            # Categorize results (Naive mapping, can be improved)
            for tech in results['all']:
                tech_lower = tech.lower()
                if tech_lower in ['laravel', 'django', 'spring boot', 'flask', 'express', 'react', 'vue.js', 'angular']:
                    if tech not in results['framework']: results['framework'].append(tech)
                elif tech_lower in ['wordpress', 'joomla', 'drupal', 'magento']:
                    if tech not in results['cms']: results['cms'].append(tech)
                elif tech_lower in ['nginx', 'apache', 'cloudflare', 'iis']:
                    if tech not in results['server']: results['server'].append(tech)
                elif tech_lower in ['php', 'python', 'java', 'go', 'ruby', 'javascript']:
                    if tech not in results['lang']: results['lang'].append(tech)

            return results

        except Exception as e:
            logger.error(f"Fingerprinting process failed for {url}: {e}")
            return results

# Standalone testing
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    fp = TechFingerprinter()
    print(json.dumps(fp.identify_tech(target), indent=2))
