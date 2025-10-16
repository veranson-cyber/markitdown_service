FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем системные зависимости для markitdown
# ffmpeg - для обработки мультимедиа и некоторых PDF
# tesseract-ocr - для OCR изображений
# poppler-utils - для работы с PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Копируем сервис в контейнер
COPY . /app

# Устанавливаем зависимости Python
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Запускаем сервис через точку входа
CMD ["python", "markitdown_service.py", "--host", "0.0.0.0", "--port", "8080"]
