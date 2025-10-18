from fastapi import APIRouter

from .depends import AnonymizeUseCase
from .schemas.data import AnonymizationData, AnonymizedData
from src.apps.auth.depends import VerifiedToken

router = APIRouter(prefix="/api/v1/anonymization", tags=["anonymization"])


@router.post("/")
async def anonymize(data: AnonymizationData, use_case: AnonymizeUseCase, auth: VerifiedToken) -> AnonymizedData:
    return await use_case(data)
