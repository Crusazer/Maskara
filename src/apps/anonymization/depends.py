from fastapi import Depends
from typing import Annotated

from src.apps.anonymization.use_cases.anonymize import AnonymizeUseCaseProtocol, AnonymizeUseCaseImpl
from src.core.services.anonymizer.depends import get_anonymizer, AnonymizerType


def get_anonymize_use_case() -> AnonymizeUseCaseProtocol:
    anonymizer = get_anonymizer(AnonymizerType.gliner)
    return AnonymizeUseCaseImpl(anonymizer)


AnonymizeUseCase = Annotated[AnonymizeUseCaseProtocol, Depends(get_anonymize_use_case)]
