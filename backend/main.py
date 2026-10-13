import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from llm_service import generate_test_cases
from schemas import GenerateRequest, GenerateResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Powered Test Case Generator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post(
    "/api/generate-test-cases",
    response_model=GenerateResponse,
)
def create_test_cases(request: GenerateRequest):
    requirement = request.requirement.strip()

    if not requirement:
        raise HTTPException(
            status_code=422,
            detail="Requirement must not be blank.",
        )

    try:
        test_cases = generate_test_cases(requirement)
        return GenerateResponse(test_cases=test_cases)

    except ValidationError:
        logger.warning(
            "AI returned test-case data that failed schema validation."
        )
        raise HTTPException(
            status_code=502,
            detail="The AI returned invalid test-case data. Please try again.",
        ) from None

    except Exception as exc:
        # Avoid exposing credentials in diagnostic logs.
        api_key = os.getenv("GEMINI_API_KEY", "")
        error_message = str(exc)

        if api_key:
            error_message = error_message.replace(
                api_key,
                "[REDACTED]",
            )

        logger.error(
            "Test-case generation failed (%s): %s",
            type(exc).__name__,
            error_message[:1500],
        )

        raise HTTPException(
            status_code=502,
            detail="Test-case generation failed. Please try again later.",
        ) from None