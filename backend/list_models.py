
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).with_name(".env"), override=True)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY is missing from backend/.env")

try:
    client = genai.Client(api_key=api_key.strip())

    for model in client.models.list():
        name = getattr(model, "name", None)
        actions = getattr(model, "supported_actions", None)

        if name and (
            not actions or "generateContent" in actions
        ):
            print(name, "| supported actions:", actions)

except Exception as exc:
    print("Could not list models.")
    print("Error type:", type(exc).__name__)
    print("Error details:", str(exc)[:1000])
