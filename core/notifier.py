import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def send_discord_alert(title: str, description: str, risk_level: str = "INFO"):
    """
    Sends a formatted alert to Discord via Webhook.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("No DISCORD_WEBHOOK_URL set. Skipping alert.")
        return

    # Color codes (Decimal)
    colors = {
        "CRITICAL": 15548997, # Red
        "HIGH": 15158332,     # Orange
        "MEDIUM": 16776960,   # Yellow
        "LOW": 3447003,       # Blue
        "INFO": 9807270       # Grey
    }
    
    color = colors.get(risk_level.upper(), 9807270)

    payload = {
        "embeds": [
            {
                "title": f"🚨 {title}",
                "description": description,
                "color": color,
                "footer": {
                    "text": f"Cassandra 2.1 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 204:
            logger.info("Discord alert sent successfully.")
        else:
            logger.error(f"Failed to send Discord alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Discord alert: {e}")
