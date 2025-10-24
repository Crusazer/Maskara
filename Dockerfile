# Dockerfile
FROM python:3.12-slim

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

# Установка uv
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir uv

WORKDIR /app

# Создаём директорию для моделей заранее (на случай, если volume пуст)
RUN mkdir -p /app/models

# Копируем зависимости
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости в виртуальное окружение
RUN uv sync --locked --no-dev

# Копируем исходный код (models/ исключён через .dockerignore)
COPY . .

# Fallback — не обязателен, так как команда задаётся в compose
CMD ["uv", "run", "python"]