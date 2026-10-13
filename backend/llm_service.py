import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from schemas import TestCase

load_dotenv(Path(__file__).with_name(".env"), override=True)

# Keep the team's selected model fixed.
MODEL_NAME = "gemini-3.8-flash"

TEST_CASE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "test_case_id": {"type": "STRING"},
            "title": {"type": "STRING"},
            "preconditions": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "test_steps": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "expected_result": {"type": "STRING"},
            "priority": {
                "type": "STRING",
                "enum": ["High", "Medium", "Low"],
            },
            "test_type": {
                "type": "STRING",
                "enum": ["Positive", "Negative"],
            },
        },
        "required": [
            "test_case_id",
            "title",
            "preconditions",
            "test_steps",
            "expected_result",
            "priority",
            "test_type",
        ],
    },
}


def _is_temporary_503(exc: Exception) -> bool:
    """Detect a temporary service-unavailable response."""
    status = getattr(exc, "code", None)

    if status is None:
        status = getattr(exc, "status_code", None)

    message = str(exc).upper()

    return (
        status == 503
        or "503 SERVICE UNAVAILABLE" in message
        or "503 UNAVAILABLE" in message
    )


def generate_test_cases(requirement: str) -> list[TestCase]:
    """Generate test cases using Gemini and validate the result."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or not api_key.strip():
        raise RuntimeError("Gemini API key is not configured.")

    client = genai.Client(api_key=api_key.strip())

    prompt = f"""
You are an experienced software test engineer.

Generate test cases for this software requirement:

{requirement}

Rules:
1. Include positive and negative cases where relevant.
2. Give each case a unique ID, such as TC001.
3. Include clear preconditions and actionable test steps.
4. State a specific expected result for each case.
5. Priority must be High, Medium, or Low.
6. Test type must be Positive or Negative.
7. Do not invent unrelated features.
8. Return at least one test case.
9. Follow the supplied JSON schema exactly.
"""

    response = None

    # Retry only temporary 503 failures, not every API error.
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TEST_CASE_SCHEMA,
                },
            )
            break

        except Exception as exc:
            if not _is_temporary_503(exc) or attempt == 2:
                raise

            # Wait 2 seconds, then 4 seconds before the final attempt.
            time.sleep(2 * (attempt + 1))

    if response is None or not response.text:
        raise ValueError("Gemini returned an empty response.")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON.") from exc

    if not isinstance(data, list) or not data:
        raise ValueError("Gemini returned an empty or invalid test-case list.")

    # Validate every generated case against our Pydantic schema.
    return [TestCase.model_validate(item) for item in data]