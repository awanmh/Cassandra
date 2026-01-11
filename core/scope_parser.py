import json
import logging
from google import genai
from config.settings import settings
from config.prompts import SCOPE_PARSER_SYSTEM_PROMPT
from core.structs import TargetConfig

class ScopeParser:
    def __init__(self):
        # Configure Gemini Client
        api_key = settings.API_KEY
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logging.warning("No API Key found. Scope parsing will fail.")

    def parse(self, policy_text: str) -> TargetConfig:
        """
        Parses the natural language policy text into a structured JSON TargetConfig.
        """
        logging.info("Parsing scope with AI...")
        
        if not self.client:
             logging.error("AI Client not initialized.")
             return TargetConfig()

        prompt = f"{SCOPE_PARSER_SYSTEM_PROMPT}\n\nPOLICY TEXT:\n{policy_text}"
        
        models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash']
        
        for model in models_to_try:
            try:
                logging.info(f"Attempting to parse with model: {model}")
                # Using the new google.genai SDK
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                
                # Extract text
                if response.text:
                    raw_json = response.text.replace("```json", "").replace("```", "").strip()
                    logging.info(f"DEBUG: Raw AI Response ({model}): {raw_json}")
                    data = json.loads(raw_json)
                    return TargetConfig(**data)
                else:
                    logging.warning(f"Empty response from AI model {model}.")
                    
            except Exception as e:
                logging.warning(f"Failed to parse scope with {model}: {e}")
                # Continue to next model
        
        logging.error("All AI models failed.")
        return TargetConfig()

scope_parser = ScopeParser()
