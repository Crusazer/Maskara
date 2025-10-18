from fastapi import APIRouter

from .depends import AnonymizeUseCase
from .schemas.data import AnonymizationData, AnonymizedData

router = APIRouter(prefix="/api/v1/anonymization", tags=["anonymization"])


@router.post("/")
async def anonymize(data: AnonymizationData, use_case: AnonymizeUseCase) -> AnonymizedData:
    return await use_case(data)
