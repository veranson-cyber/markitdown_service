MarkItDown conversion service

Это минимальный контейнер для запуска локального сервиса конвертации документов в Markdown на основе скрипта `markitdown_service.py`.

Быстрый старт (Docker):

1) Перейдите в директорию `markitdown_service`:
   - Windows PowerShell:
     cd .\markitdown_service

2) Запустите сервис через docker-compose:
   docker compose up --build

   Сервис будет доступен на http://localhost:8080

Основные эндпоинты:
- GET /health — проверка состояния сервиса
- POST /convert — загрузить файл и получить Markdown (multipart/form-data, поле `file`)
- GET /supported-formats — список поддерживаемых форматов

Запуск без докера (локально):
- Установите зависимости:
  python -m pip install -r requirements.txt
- Запустите:
  python markitdown_service.py --host 0.0.0.0 --port 8080

Примечания:
- По умолчанию сервис слушает на 0.0.0.0 (в контейнере это нормально). Для локального использования с привязкой к localhost используйте `--host 127.0.0.1`.
- Убедитесь, что пакет `markitdown` доступен в окружении — он выполняет основную конвертацию документов.
- В контейнере можно пробросить дополнительную директорию `./static` через volumes, если хотите заменить Swagger UI файлы.
