import requests
import logging
from config.settings import settings

def send_alert(title, vulnerability_type, proof, risk_level):
    """
    Sends an alert to Discord via Webhook.
    """
    if not settings.DISCORD_WEBHOOK_URL:
        logging.warning("Discord Webhook URL not set. Skipping notification.")
        return

    color = 16711680 if risk_level.upper() in ["HIGH", "CRITICAL"] else 3447003 # Red or Blue

    embed = {
        "title": f"[{risk_level}] {title}",
        "description": f"**Type:** {vulnerability_type}\n**Proof:** `{proof}`",
        "color": color,
        "footer": {"text": "Cassandra Ultimate Scanner"}
    }
    
    payload = {
        "username": "Cassandra Bot",
        "embeds": [embed]
    }

    try:
        requests.post(settings.DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Failed to send Discord alert: {e}")
