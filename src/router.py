"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI

from src.apps.anonymization.router import router as assistants_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(assistants_router)
    return app
