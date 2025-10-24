from pydantic import Field

from src.core.schemas import InputApiSchema, OutputApiSchema


class AnonymizationData(InputApiSchema):
    text: str
    labels: list[str]
    threshold: float = Field(..., gt=0, le=1)
    exclude_lemmas: list[str]


class AnonymizedData(OutputApiSchema):
    text: str
    anonymization_map: dict[str, dict[str, str]]
