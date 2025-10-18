"""
Основной модуль для middleware приложения.
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .settings import settings


def apply_middleware(app: FastAPI) -> FastAPI:
    """
    Применяем middleware.
    """
    app.add_middleware(
        CORSMiddleware, # type: ignore
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    return app
