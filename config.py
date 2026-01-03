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
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
RECRAFT_API_KEY = os.getenv("RECRAFT_API_KEY")

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    # base_url="https://api.deepseek.com/v3.2_speciale_expires_on_20251215",
)

grok_client = Client(
    api_key=GROK_API_KEY,
    timeout=3600,
)

# AWS S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_REGION = os.getenv("AWS_S3_REGION", "ap-northeast-2")
