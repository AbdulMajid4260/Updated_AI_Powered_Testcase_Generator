from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(
        min_length=1,
        description="The software requirement for test-case generation",
    )


class TestCase(BaseModel):
    __test__ = False
    model_config = ConfigDict(extra="forbid")

    test_case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    preconditions: list[str]
    test_steps: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    priority: Literal["High", "Medium", "Low"]
    test_type: Literal["Positive", "Negative"]


class GenerateResponse(BaseModel):
    test_cases: list[TestCase] = Field(min_length=1)