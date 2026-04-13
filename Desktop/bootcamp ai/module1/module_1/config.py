import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

def get_llm_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY manquante dans .env")
    return anthropic.Anthropic(api_key=api_key)