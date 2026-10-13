from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
from schemas import TestCase as TestCaseSchema


client = TestClient(main.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_empty_requirement_is_rejected():
    response = client.post(
        "/api/generate-test-cases",
        json={"requirement": "   "},
    )

    assert response.status_code == 422


def test_missing_requirement_is_rejected():
    response = client.post(
        "/api/generate-test-cases",
        json={},
    )

    assert response.status_code == 422


def test_unknown_request_field_is_rejected():
    response = client.post(
        "/api/generate-test-cases",
        json={
            "requirement": "Users can log in.",
            "extra_field": "unexpected",
        },
    )

    assert response.status_code == 422


def test_generate_test_cases_successfully(monkeypatch):
    fake_test_cases = [
        TestCaseSchema(
            test_case_id="TC001",
            title="Login with valid credentials",
            preconditions=["A registered user exists"],
            test_steps=[
                "Open the login page",
                "Enter a registered email and correct password",
                "Click the Login button",
            ],
            expected_result="The user is redirected to the dashboard",
            priority="High",
            test_type="Positive",
        )
    ]

    def fake_generate_test_cases(requirement):
        assert "log in" in requirement.lower()
        return fake_test_cases

    monkeypatch.setattr(
        main,
        "generate_test_cases",
        fake_generate_test_cases,
    )

    response = client.post(
        "/api/generate-test-cases",
        json={
            "requirement": "Users can log in with valid credentials."
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert len(body["test_cases"]) == 1
    assert body["test_cases"][0]["test_case_id"] == "TC001"
    assert body["test_cases"][0]["priority"] == "High"
    assert body["test_cases"][0]["test_type"] == "Positive"


def test_gemini_failure_returns_502(monkeypatch):
    def fake_generate_test_cases(requirement):
        raise RuntimeError("Simulated Gemini failure")

    monkeypatch.setattr(
        main,
        "generate_test_cases",
        fake_generate_test_cases,
    )

    response = client.post(
        "/api/generate-test-cases",
        json={"requirement": "Users can log in."},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Test-case generation failed. Please try again later."
    }


def test_invalid_ai_data_returns_502(monkeypatch):
    def fake_generate_test_cases(requirement):
        # Deliberately invalid: required test-case fields are missing.
        return [
            TestCaseSchema.model_validate(
                {"test_case_id": "TC001"}
            )
        ]

    monkeypatch.setattr(
        main,
        "generate_test_cases",
        fake_generate_test_cases,
    )

    response = client.post(
        "/api/generate-test-cases",
        json={"requirement": "Users can log in."},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The AI returned invalid test-case data. Please try again."
    }