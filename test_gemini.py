import os
import sys
from dotenv import load_dotenv
from config.settings import settings
from google import genai

# Force load Env
load_dotenv()

try:
    print("Initializing Client...")
    client = genai.Client(api_key=settings.API_KEY)
    
    models = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-2.0-flash-exp']
    
    for m in models:
        print(f"\n--- Testing {m} ---")
        try:
            response = client.models.generate_content(
                model=m,
                contents="Hello, are you working?"
            )
            print("Response Received!")
            print(f"Text: {response.text}")
            break # Stop if one works
        except Exception as e:
            print(f"FAILED {m}: {repr(e)}")

except Exception as e:
    print(f"GLOBAL ERROR: {repr(e)}")
