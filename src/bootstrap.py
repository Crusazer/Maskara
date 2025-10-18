from contextlib import asynccontextmanager

from fastapi import FastAPI

from .logging import set_logging
from .middlware import apply_middleware
from .router import apply_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Предварительная инициализация приложения.
    А так же корректное освобождение ресурсов при завершении работы приложения.
    """
    # Инициализация ресурсов
    set_logging()
    yield
    # Освобождение ресурсов


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app = apply_routes(apply_middleware(app))
    return app
