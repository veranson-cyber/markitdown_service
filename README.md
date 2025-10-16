# MarkItDown — Docker сервис

Сервис для конвертации различных форматов документов в Markdown, оптимизированный для использования с ИИ-системами и большими языковыми моделями (LLM).

Основан на библиотеке [markitdown](https://github.com/microsoft/markitdown) от Microsoft. Преобразует документы Office, PDF, HTML, изображения и другие форматы в чистый Markdown, который легко обрабатывается ИИ-моделями для извлечения информации, анализа и генерации ответов.

**Основные возможности:**
- 🔄 Конвертация 15+ форматов документов в Markdown
- ⚡ Высокая производительность благодаря пулам воркеров (потоки + процессы)
- 🐳 Готовый Docker-образ для быстрого развёртывания
- 📚 Swagger UI документация из коробки
- 🔌 Простое проксирование через nginx с единым префиксом `/convert`
- 🤖 Оптимизирован для работы с RAG-системами и AI-ассистентами

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

Сервис можно легко интегрировать в существующую инфраструктуру через nginx. Все эндпоинты доступны по префиксу `/convert`, что упрощает настройку reverse proxy.

**Пример конфигурации nginx:**

```nginx
# Основные эндпоинты API
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
    
    # Замените на адрес вашего контейнера
    proxy_pass http://localhost:8080/convert/;
}

# Статические файлы (Swagger UI)
location /static/ {
    proxy_pass http://localhost:8080/static/;
}
```

После настройки nginx сервис будет доступен по адресу: `https://your-domain.com/convert/docs`

**Дополнительные настройки для больших файлов:**

```nginx
# Увеличение лимита размера загружаемых файлов
client_max_body_size 100M;

# Таймауты для обработки больших документов
proxy_connect_timeout 300;
proxy_send_timeout 300;
proxy_read_timeout 300;
send_timeout 300;
```

## Примечание

Документация про внутренние параметры запуска (например, упоминание `markitdown_service.py` или настроек хоста) опущена — предполагается запуск через Docker/Compose и проброс нужных портов/volumes.

## Использование с ИИ-системами

Этот сервис идеально подходит для интеграции с AI-ассистентами и RAG-системами:

**Типичные сценарии использования:**

1. **RAG (Retrieval-Augmented Generation)**
   - Конвертация корпоративных документов в Markdown
   - Индексация содержимого для векторных баз данных
   - Подготовка контекста для LLM

2. **AI-ассистенты**
   - Обработка загруженных пользователем документов
   - Извлечение информации из PDF, DOCX, PPTX
   - Анализ содержимого изображений с помощью OCR

3. **Автоматизация документооборота**
   - Пакетная обработка документов
   - Извлечение структурированных данных
   - Подготовка данных для обучения моделей

**Пример интеграции с Python:**

```python
import requests

# Загрузка и конвертация документа
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/convert/upload',
        files={'file': f}
    )

result = response.json()
markdown_content = result['content']

# Использование с LLM (например, OpenAI)
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Ты помощник для анализа документов."},
        {"role": "user", "content": f"Проанализируй документ:\n\n{markdown_content}"}
    ]
)

print(completion.choices[0].message.content)
```

## Технические характеристики

- **Язык:** Python 3.11
- **Фреймворк:** FastAPI + Uvicorn
- **Библиотека конвертации:** markitdown[all]
- **Производительность:** Пулы воркеров (потоки для файлов <1MB, процессы для больших файлов)
- **Контейнеризация:** Docker + Docker Compose
- **API:** REST API + Swagger UI документация
