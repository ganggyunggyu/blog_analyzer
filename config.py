import os
from dotenv import load_dotenv
from openai import OpenAI
from xai_sdk import Client

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

solar_client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1/solar",
    default_headers={"Authorization": f"Bearer {UPSTAGE_API_KEY}"},
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

grok_client = Client(
    api_key=GROK_API_KEY,
    timeout=3600,
)
