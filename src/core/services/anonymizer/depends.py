from enum import StrEnum

from src.settings import settings
from .base import Anonymizer
from .gliner.gliner import get_gliner


class AnonymizerType(StrEnum):
    gliner = "gliner"


def get_anonymizer(anonymizer_type: AnonymizerType) -> Anonymizer:
    if anonymizer_type == AnonymizerType.gliner:
        return get_gliner(settings.GLINER_MODEL)
    raise ValueError("Unexpected anonymizer type")
