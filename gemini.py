import os
from dotenv import load_dotenv
import google.genai as genai

# Load .env supaya GOOGLE_API_KEY terbaca
load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# List semua model yang tersedia untuk API key kamu
for model in client.models.list():
    print(model.name, model.supported_actions)

# Contoh pakai salah satu model
model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content("Hello Gemini! Tes generate content.")
print(response.text)
