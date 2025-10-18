FROM python:3.12-slim

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Установка uv
RUN pip install --upgrade pip && pip install uv

WORKDIR /app

# Сначала копируем зависимости — для кэширования
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости из lock-файла
RUN uv sync --locked --no-dev

# Копируем всё остальное (исключая .dockerignore)
COPY . .

# По умолчанию ничего не запускаем — команды задаются в docker-compose
CMD ["uv", "run", "python"]