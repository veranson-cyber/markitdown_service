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

### GET /health

Проверка состояния сервиса.

**Пример (Linux/macOS):**

```bash
curl http://localhost:8080/health
```

**Пример (Windows PowerShell):**

```powershell
Invoke-RestMethod -Uri http://localhost:8080/health
```

**Ответ:**

```json
{"status": "ok"}
```

---

### POST /convert

Загрузить файл и получить Markdown.

**Параметры:**
- `file` (обязательный): файл для конвертации (multipart/form-data)

**Пример (Linux/macOS):**

```bash
curl -X POST http://localhost:8080/convert \
  -F "file=@/path/to/document.pdf"
```

**Пример (Windows PowerShell):**

```powershell
$filePath = "C:\path\to\document.pdf"
$uri = "http://localhost:8080/convert"
$form = @{
    file = Get-Item -Path $filePath
}
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

**Ответ (JSON):**

```json
{
  "markdown": "# Документ\n\nСодержимое...",
  "title": "document.pdf",
  "metadata": {}
}
```

---

### GET /supported-formats

Получить список поддерживаемых форматов.

**Пример (Linux/macOS):**

```bash
curl http://localhost:8080/supported-formats
```

**Пример (Windows PowerShell):**

```powershell
Invoke-RestMethod -Uri http://localhost:8080/supported-formats
```

**Ответ:**

```json
{
  "formats": [".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".jpg", ".jpeg", ".png", ".zip", ".csv", ".json", ".xml", ".txt", ".md"]
}
```

## Замена статических файлов

Чтобы заменить Swagger UI или другие статические файлы, пробросьте локальную папку `./static` в контейнер через volumes в `docker-compose.yml` или через `-v` при `docker run`.

## Примечание

Документация про внутренние параметры запуска (например, упоминание `markitdown_service.py` или настроек хоста) опущена — предполагается запуск через Docker/Compose и проброс нужных портов/volumes.
