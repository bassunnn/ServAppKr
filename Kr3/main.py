from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager

import database
from config import get_settings
from routers import auth as auth_router, todos, admin
from security import verify_docs_credentials

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация БД при старте
    database.init_db()
    yield


# Создаём приложение с условной конфигурацией документации
if settings.MODE == "DEV":
    app = FastAPI(
        title="Kr3 API",
        description="Контрольная работа №3 - FastAPI Authentication & RBAC",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/docs", include_in_schema=False)
    async def get_docs(username: str = Depends(verify_docs_credentials)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="Kr3 API Docs")

    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_json(username: str = Depends(verify_docs_credentials)):
        return app.openapi()
else:
    # PROD - документация отключена
    app = FastAPI(
        title="Kr3 API",
        description="Контрольная работа №3 - FastAPI Authentication & RBAC",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

# Подключаем роутеры
app.include_router(auth_router.router)
app.include_router(todos.router)
app.include_router(admin.router)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to Kr3 API", "mode": settings.MODE}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
