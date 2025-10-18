from typing import Protocol

from src.apps.anonymization.schemas.data import AnonymizationData, AnonymizedData
from src.core.services.anonymizer.base import Anonymizer


class AnonymizeUseCaseProtocol(Protocol):
    async def __call__(self, data: AnonymizationData) -> AnonymizedData: ...


class AnonymizeUseCaseImpl:
    def __init__(self, anonymizer: Anonymizer) -> None:
        self.anonymizer = anonymizer

    async def __call__(self, data: AnonymizationData) -> AnonymizedData:
        exclude = {word.lower() for word in data.exclude_lemmas}
        result = await self.anonymizer.anonymize(data.text, data.labels, data.threshold, set(exclude))
        return AnonymizedData(
            text=result.text,
            anonymization_map=result.map,
        )
