FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Копируем сервис в контейнер
COPY . /app

# Устанавливаем зависимости
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Запускаем сервис через точку входа
CMD ["python", "markitdown_service.py", "--host", "0.0.0.0", "--port", "8080"]
