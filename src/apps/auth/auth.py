from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.settings import settings

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> None:
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
