#!/usr/bin/env python3
"""
MarkItDown conversion service - FastAPI микросервис для конвертации документов в Markdown
Объединяет производительность (пулы воркеров) с простотой использования
"""

import argparse
import logging
import os
import tempfile
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки производительности
MAX_WORKERS = min(32, (os.cpu_count() or 1) + 4)  # Оптимальное количество потоков
PROCESS_POOL_SIZE = min(4, os.cpu_count() or 1)    # Количество процессов для CPU-интенсивных задач

# Создаем пулы воркеров
thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
process_pool = ProcessPoolExecutor(max_workers=PROCESS_POOL_SIZE)

logger.info(f"Инициализированы пулы воркеров: {MAX_WORKERS} потоков, {PROCESS_POOL_SIZE} процессов")

# Список поддерживаемых форматов
SUPPORTED_FORMATS = [
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".doc", ".ppt",
    ".html", ".htm",
    ".jpg", ".jpeg", ".png",
    ".zip",
    ".csv", ".tsv",
    ".json", ".xml",
    ".txt", ".md", ".rtf",
    ".eml", ".msg"
]

# Pydantic-модель для ответа
class DocumentOutput(BaseModel):
    filename: str
    content: str
    format: str = "markdown"
    processing_time: float = 0.0
    file_size: int = 0


def process_with_markitdown_sync(file_path: str, filename: str) -> dict:
    """
    Синхронная функция для обработки документа с помощью markitdown.
    Используется в пуле процессов для параллельной обработки.
    """
    start_time = time.time()
    
    try:
        from markitdown import MarkItDown
        
        # Инициализируем с включённым OCR для изображений и отсканированных PDF
        md = MarkItDown(enable_ocr=True)
        result = md.convert(file_path)

        # Извлекаем текст из результата
        content = (
            getattr(result, "text_content", None)
            or getattr(result, "markdown", None)
            or str(result)
        )
        
        processing_time = time.time() - start_time
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return {
            "success": True,
            "filename": filename or "document",
            "content": content or "",
            "format": "markdown",
            "processing_time": processing_time,
            "file_size": file_size
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка markitdown при обработке {filename}: {e}")
        return {
            "success": False,
            "filename": filename or "document",
            "content": "",
            "format": "markdown", 
            "error": str(e),
            "processing_time": processing_time,
            "file_size": 0
        }


async def process_with_markitdown(file_bytes: bytes, filename: str) -> DocumentOutput:
    """
    Асинхронная обработка документа с использованием пулов воркеров.
    Большие файлы (>1MB) обрабатываются в процессном пуле.
    """
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Пустой входной файл")

    tmp_path = None
    try:
        # Создаём временный файл
        suffix = os.path.splitext(filename or "")[1] or ""
        with tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False) as tf:
            tf.write(file_bytes)
            tf.flush()
            tmp_path = tf.name

        # Определяем, использовать ли процессный пул для больших файлов
        file_size = len(file_bytes)
        use_process_pool = file_size > 1024 * 1024  # Больше 1MB - процессный пул
        
        if use_process_pool:
            logger.info(f"Обработка большого файла {filename} ({file_size/1024/1024:.1f}MB) в процессном пуле")
            loop = asyncio.get_event_loop()
            result_dict = await loop.run_in_executor(
                process_pool, 
                process_with_markitdown_sync, 
                tmp_path, 
                filename
            )
        else:
            logger.info(f"Обработка файла {filename} ({file_size/1024:.1f}KB) в потоковом пуле")
            loop = asyncio.get_event_loop()
            result_dict = await loop.run_in_executor(
                thread_pool, 
                process_with_markitdown_sync, 
                tmp_path, 
                filename
            )
        
        if not result_dict["success"]:
            raise HTTPException(status_code=500, detail=f"Ошибка конвертации: {result_dict.get('error', 'Неизвестная ошибка')}")
        
        return DocumentOutput(
            filename=result_dict["filename"],
            content=result_dict["content"],
            format=result_dict["format"],
            processing_time=result_dict["processing_time"],
            file_size=result_dict["file_size"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка конвертации: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# Создание FastAPI приложения
app = FastAPI(
    title="MarkItDown Document Converter API",
    description="API для конвертации документов в формат Markdown. Поддерживает DOCX, PPTX, XLSX, PDF, HTML, изображения и другие форматы.",
    version="1.0.0",
    docs_url=None,  # Отключаем стандартный Swagger UI
    redoc_url=None,
    openapi_url="/convert/openapi.json"
)

# Кастомизация OpenAPI схемы
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.2"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Монтирование статических файлов
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", include_in_schema=False)
async def root():
    """Корневой эндпоинт - редирект на документацию"""
    return RedirectResponse(url="/convert/docs")

@app.get("/convert/", include_in_schema=False)
async def redirect_to_docs():
    """Перенаправляет корневой URL на документацию"""
    return RedirectResponse(url="/convert/docs")


@app.get("/convert/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Возвращает кастомный Swagger UI с локальными файлами"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>MarkItDown API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="/static/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
            .swagger-ui .topbar { display: none }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="/static/swagger-ui-bundle.js"></script>
        <script src="/static/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                try {
                    window.ui = SwaggerUIBundle({
                        url: "/convert/openapi.json",
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                        plugins: [SwaggerUIBundle.plugins.DownloadUrl],
                        layout: "StandaloneLayout",
                        defaultModelsExpandDepth: -1,
                        validatorUrl: null,
                        tryItOutEnabled: true
                    });
                } catch (error) {
                    console.error('Ошибка загрузки Swagger UI:', error);
                    document.getElementById('swagger-ui').innerHTML = 
                        '<div style="padding: 20px; text-align: center;">' +
                        '<h2>MarkItDown API</h2>' +
                        '<p>Swagger UI не загружен. Используйте прямые запросы:</p>' +
                        '<ul style="text-align: left; display: inline-block;">' +
                        '<li>GET /convert/health - проверка состояния</li>' +
                        '<li>GET /convert/supported-formats - поддерживаемые форматы</li>' +
                        '<li>POST /convert/upload - конвертация документа</li>' +
                        '</ul></div>';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/convert/health", 
         summary="Проверка состояния сервиса",
         description="Проверка работоспособности API")
async def health_check():
    """Проверка работоспособности сервиса"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "markitdown-converter",
            "version": "1.0.0",
            "workers": {"threads": MAX_WORKERS, "processes": PROCESS_POOL_SIZE}
        },
        status_code=200
    )


@app.get("/convert/supported-formats",
         summary="Список поддерживаемых форматов",
         description="Возвращает список форматов файлов, которые поддерживает сервис")
async def get_supported_formats():
    """Получить список поддерживаемых форматов файлов"""
    return JSONResponse(
        content={
            "supported_formats": SUPPORTED_FORMATS,
            "count": len(SUPPORTED_FORMATS),
            "description": "Форматы файлов, поддерживаемые для конвертации в Markdown",
            "note": "Для OCR (изображений) могут потребоваться дополнительные зависимости (например, Tesseract)"
        },
        status_code=200
    )


@app.post("/convert/upload",
          response_model=DocumentOutput,
          summary="Конвертация документа в Markdown",
          description="Принимает файл любого поддерживаемого формата (документы, изображения, PDF, HTML, архивы, текст, csv, json, xml) и возвращает его содержимое в Markdown",
          responses={
              200: {
                  "description": "Успешная конвертация",
                  "content": {
                      "application/json": {
                          "example": {
                              "filename": "document.docx",
                              "content": "# Заголовок\n\nСодержимое документа...",
                              "format": "markdown",
                              "processing_time": 0.5,
                              "file_size": 12345
                          }
                      }
                  }
              },
              400: {"description": "Некорректный файл или неподдерживаемый формат"},
              500: {"description": "Ошибка сервера при обработке файла"}
          })
async def convert_document(
    file: UploadFile = File(..., description="Файл документа для конвертации в Markdown")
):
    """
    Конвертирует загруженный документ в формат Markdown.
    Использует пулы воркеров для оптимальной производительности.
    """
    start_time = time.time()
    logger.info(f"Получен запрос на конвертацию файла: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла не указано")
    
    # Проверка расширения файла
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат: {file_ext}. Поддерживаемые: {', '.join(SUPPORTED_FORMATS)}"
        )

    try:
        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Файл пуст")

        # Обрабатываем файл асинхронно
        result = await process_with_markitdown(file_bytes, file.filename)
        
        total_time = time.time() - start_time
        logger.info(f"Успешно обработан файл: {file.filename} за {total_time:.2f}s (обработка: {result.processing_time:.2f}s)")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Непредвиденная ошибка при обработке {file.filename} за {total_time:.2f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")


def main():
    """Точка входа для запуска сервиса"""
    parser = argparse.ArgumentParser(description="MarkItDown Conversion Service")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host для сервера (по умолчанию: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Порт для сервера (по умолчанию: 8080)")
    parser.add_argument("--reload", action="store_true", help="Включить auto-reload для разработки")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Запуск MarkItDown Service на http://{args.host}:{args.port}")
    logger.info(f"📚 Документация API: http://{args.host}:{args.port}/docs")
    logger.info(f"⚡ Настройки производительности: {MAX_WORKERS} потоков, {PROCESS_POOL_SIZE} процессов")
    
    try:
        uvicorn.run(
            "markitdown_service:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, останавливаем сервер...")
    finally:
        # Корректно закрываем пулы воркеров
        logger.info("Закрытие пулов воркеров...")
        try:
            thread_pool.shutdown(wait=True)
            process_pool.shutdown(wait=True)
            logger.info("Пулы воркеров закрыты")
        except Exception as e:
            logger.error(f"Ошибка при закрытии пулов воркеров: {e}")


if __name__ == "__main__":
    main()
