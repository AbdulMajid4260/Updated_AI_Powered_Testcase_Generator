
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Load the .env file located beside this script.
load_dotenv(Path(__file__).with_name(".env"), override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key or not api_key.strip():
    print("CONFIGURATION ERROR: GEMINI_API_KEY is missing or empty.")
    raise SystemExit(1)

try:
    client = genai.Client(api_key=api_key.strip())

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Reply with exactly: Gemini connection successful",
    )

    if response.text:
        print("SUCCESS: Gemini API call completed.")
        print("Model response:", response.text)
    else:
        print("WARNING: Gemini returned no text.")

except Exception as exc:
    # Redact the key in case an exception message contains it.
    message = str(exc).replace(api_key, "[REDACTED]")
    print("GEMINI API TEST FAILED")
    print("Error type:", type(exc).__name__)
    print("Error details:", message[:1500])

