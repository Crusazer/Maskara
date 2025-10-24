from typing import Protocol
from .schemas import AnonymizationResult


class Anonymizer(Protocol):
    async def anonymize(
        self, text: str, labels: list[str], threshold: float, exclude_lemmas: set[str] | None = None
    ) -> AnonymizationResult: ...
