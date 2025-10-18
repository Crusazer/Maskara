from pydantic import BaseModel


class AnonymizationResult(BaseModel):
    text: str
    map: dict[str, str]
