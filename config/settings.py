import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load Secrets
env_path = BASE_DIR / ".env" # Prefer root .env first
if not env_path.exists():
    env_path = BASE_DIR / "config" / "secrets.env"

load_dotenv(env_path, override=True)

class Settings:
    # API Keys
    OPENAI_API_KEY = os.getenv("GEMINI_API_KEY") # User said GEMINI_API_KEY implies using Gemini usually, but prompts say OpenAI API. Sticking to user request var name mapped to OpenAI client if compatible or just generic.
    # Note: User request explicitly said "AI: OpenAI API (Structured Outputs)".
    # But user provided "gemini key : AIzaSy..." in the request.
    # I should probably use the OpenAI client but pointing to Gemini if that's what they want, OR they meant they have a Gemini key.
    # Given the prompt "AI: OpenAI API (Structured Outputs)", and the key "AIzaSy...", it looks like a Google AI key.
    # However, for "Structured Outputs" strictly, OpenAI is best. 
    # But since I must use the provided key, and it's a Gemini key, I will assume we might need to use a compatible client or just use the key as OPENAI_API_KEY if they are using an adapter, OR I should name it properly.
    # Let's stick to loading it as OPENAI_API_KEY for the code to work if they swap it, or I'll name it API_KEY.
    # Actually, let's just load it as 'OPENAI_API_KEY' but check for 'GEMINI_API_KEY' in env to be safe.
    
    API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

    # Tool Paths (Optional if in PATH)
    SQLMAP_PATH = os.getenv("SQLMAP_PATH", "sqlmap") # Default to 'sqlmap' command

    # Paths
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)
    
    LOGS_DIR = DATA_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

    # Proxy
    PROXY_URL = os.getenv("PROXY_URL", None) # e.g. http://127.0.0.1:8080 for Burp

settings = Settings()
