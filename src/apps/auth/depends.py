from typing import Annotated
from fastapi import Depends
from .auth import verify_token

VerifiedToken = Annotated[None, Depends(verify_token)]
