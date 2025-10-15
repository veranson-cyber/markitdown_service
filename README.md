# MarkItDown — Docker сервис

Минимальный Docker-контейнер для конвертации документов в Markdown.

## Быстрый запуск

Из корня проекта (где находятся `docker-compose.yml` и `Dockerfile`):

Windows PowerShell:

```powershell
# Cобрать и запустить через Docker Compose в фоновом режиме
docker compose up --build -d

# Остановить и удалить контейнеры
docker compose down

# Альтернатива — сборка и запуск образа вручную
docker build -t markitdown:latest .
docker run -p 8080:8080 --rm markitdown:latest
```

Linux / macOS (bash):

```bash
# Cобрать и запустить через Docker Compose в фоне
docker compose up --build -d

# Остановить и удалить контейнеры
docker compose down

# Альтернатива — сборка и запуск образа вручную
docker build -t markitdown:latest .
docker run -p 8080:8080 --rm markitdown:latest
```

Сервис будет доступен на проброшенном порту на хосте (пример: http://localhost:8080).

**Важно**: Все эндпоинты доступны по префиксу `/convert`, что упрощает проксирование через nginx.

## Поддерживаемые форматы

Сервис использует библиотеку **markitdown** (Microsoft) для конвертации различных форматов документов в Markdown.

### Входные форматы

- **Документы Office**: `.docx`, `.pptx`, `.xlsx`
- **PDF**: `.pdf` (текст и таблицы)
- **HTML**: `.html`, `.htm`
- **Изображения**: `.jpg`, `.jpeg`, `.png` (с OCR, если доступна библиотека Tesseract)
- **ZIP-архивы**: `.zip` (извлечение и конвертация содержимого)
- **CSV**: `.csv`
- **JSON/XML**: `.json`, `.xml`
- **Текстовые**: `.txt`, `.md`

**Примечание**: Для OCR (изображений) могут потребоваться дополнительные зависимости (например, Tesseract). Уточните конфигурацию в коде сервиса или проверьте ответ эндпоинта `/supported-formats`.

### Формат ответа

Эндпоинт `/convert` возвращает JSON:

```json
{
  "markdown": "# Заголовок\n\nТекст документа...",
  "title": "Название документа (если доступно)",
  "metadata": {}
}
```

Или текстовый ответ (зависит от параметров запроса).

## Основные HTTP-эндпоинты

Все эндпоинты доступны по префиксу `/convert`.

### GET /convert/health

Проверка состояния сервиса.

**Пример (Linux/macOS):**

```bash
curl http://localhost:8080/convert/health
```

**Пример (Windows PowerShell):**

```powershell
Invoke-RestMethod -Uri http://localhost:8080/convert/health
```

**Ответ:**

```json
{"status": "healthy", "service": "markitdown-converter", "version": "1.0.0"}
```

---

### POST /convert/upload

Загрузить файл и получить Markdown.

**Параметры:**
- `file` (обязательный): файл для конвертации (multipart/form-data)

**Пример (Linux/macOS):**

```bash
curl -X POST http://localhost:8080/convert/upload \
  -F "file=@/path/to/document.pdf"
```

**Пример (Windows PowerShell):**

```powershell
$filePath = "C:\path\to\document.pdf"
$uri = "http://localhost:8080/convert/upload"
$form = @{
    file = Get-Item -Path $filePath
}
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

**Ответ (JSON):**

```json
{
  "filename": "document.pdf",
  "content": "# Документ\n\nСодержимое...",
  "format": "markdown",
  "processing_time": 0.5,
  "file_size": 12345
}
```

---

### GET /convert/supported-formats

Получить список поддерживаемых форматов.

**Пример (Linux/macOS):**

```bash
curl http://localhost:8080/convert/supported-formats
```

**Пример (Windows PowerShell):**

```powershell
Invoke-RestMethod -Uri http://localhost:8080/convert/supported-formats
```

**Ответ:**

```json
{
  "supported_formats": [".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".jpg", ".jpeg", ".png", ".zip", ".csv", ".json", ".xml", ".txt", ".md"],
  "count": 15
}
```

---

### GET /convert/docs

Swagger UI документация (интерактивная).

## Замена статических файлов

Чтобы заменить Swagger UI или другие статические файлы, пробросьте локальную папку `./static` в контейнер через volumes в `docker-compose.yml` или через `-v` при `docker run`.

## Проксирование через nginx

Пример конфигурации nginx для проксирования сервиса:

```nginx
location /convert/ {
    proxy_buffering off;
    proxy_redirect off;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /convert;
    proxy_pass http://172.30.1.117:8080/convert/;
}

location /static/ {
    proxy_pass http://172.30.1.117:8080/static/;
}
```

Теперь сервис будет доступен по адресу: `https://your-domain.com/convert/docs`

## Примечание

Документация про внутренние параметры запуска (например, упоминание `markitdown_service.py` или настроек хоста) опущена — предполагается запуск через Docker/Compose и проброс нужных портов/volumes.
