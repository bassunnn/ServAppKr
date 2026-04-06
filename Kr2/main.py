from fastapi import FastAPI, Response, Request, Depends, HTTPException, Header
from pydantic import EmailStr, Field
import uuid
import time
from itsdangerous import URLSafeSerializer
from typing import Optional
from datetime import datetime

from models import UserCreate, LoginRequest, CommonHeaders

app = FastAPI(title="Контрольная работа №2")

SECRET_KEY = "my-secret-key-for-control-work"
signer = URLSafeSerializer(SECRET_KEY)

# Задача 5.1: Хранилище сессий
sessions = {}

# Задача 3.2: Список образцов продуктов
SAMPLE_PRODUCTS = [
    {"product_id": 1, "name": "Ноутбук HP", "category": "Электроника", "price": 50000},
    {"product_id": 2, "name": "Смартфон Samsung", "category": "Электроника", "price": 30000},
    {"product_id": 3, "name": "Кроссовки Nike", "category": "Обувь", "price": 8000},
    {"product_id": 4, "name": "Куртка зимняя", "category": "Одежда", "price": 12000},
    {"product_id": 5, "name": "Наушники Sony", "category": "Электроника", "price": 15000},
    {"product_id": 6, "name": "Рюкзак городской", "category": "Аксессуары", "price": 3500},
    {"product_id": 7, "name": "Клавиатура Logitech", "category": "Электроника", "price": 5000},
    {"product_id": 8, "name": "Ботинки Timberland", "category": "Обувь", "price": 14000},
    {"product_id": 9, "name": "Монитор Dell", "category": "Электроника", "price": 25000},
    {"product_id": 10, "name": "Футболка Adidas", "category": "Одежда", "price": 2500},
]


# Задача 3.1
@app.post("/create_user")
async def create_user(user: UserCreate):
    """Создание пользователя с валидацией данных"""
    return user.dict()


# Задача 3.2
@app.get("/products/search")
async def search_products(
    keyword: str,
    category: Optional[str] = None,
    limit: Optional[int] = 10
):
    """Поиск продуктов по ключевому слову и категории"""
    results = []
    for product in SAMPLE_PRODUCTS:
        name_match = keyword.lower() in product["name"].lower()
        category_match = True
        if category:
            category_match = product["category"] == category
        
        if name_match and category_match:
            results.append(product)
        
        if len(results) >= limit:
            break
    
    return results


@app.get("/product/{product_id}")
async def get_product(product_id: int):
    """Получение продукта по ID"""
    for product in SAMPLE_PRODUCTS:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


# Задача 5.1
@app.post("/login_v1")
async def login_v1(login_data: LoginRequest, response: Response):
    """Простая cookie-аутентификация (Задание 5.1)"""
    if login_data.username == "user123" and login_data.password == "password123":
        session_token = str(uuid.uuid4())
        sessions[session_token] = {"username": login_data.username}
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=3600,
            secure=False
        )
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/user")
async def get_user(request: Request, response: Response):
    """Получение данных пользователя из cookie (Задание 5.1)"""
    session_token = request.cookies.get("session_token")
    if session_token and session_token in sessions:
        return {"username": sessions[session_token]["username"]}
    response.status_code = 401
    return {"message": "Unauthorized"}


# Задача 5.2
@app.post("/login_v2")
async def login_v2(login_data: LoginRequest, response: Response):
    """Аутентификация с подписанными cookie (Задание 5.2)"""
    if login_data.username == "user123" and login_data.password == "password123":
        user_id = str(uuid.uuid4())
        signed_value = signer.dumps(user_id)
        response.set_cookie(
            key="session_token",
            value=signed_value,
            httponly=True,
            max_age=3600,
            secure=False
        )
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/profile_v2")
async def profile_v2(request: Request, response: Response):
    """Профиль с проверкой подписанной cookie (Задание 5.2)"""
    token = request.cookies.get("session_token")
    if not token:
        response.status_code = 401
        return {"message": "Unauthorized"}
    
    try:
        user_id = signer.loads(token, max_age=3600)
        return {"user_id": user_id, "message": "Profile data"}
    except Exception:
        response.status_code = 401
        return {"message": "Unauthorized"}


#Задача 5.3
async def get_current_user(request: Request, response: Response):
    """Dependency для проверки и продления сессии (Задание 5.3)"""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Unauthorized")
    
    try:
        decoded = signer.loads(token)
        user_id, ts_str = decoded.rsplit('.', 1)
        ts = int(ts_str)
        now = int(time.time())
        age = now - ts
        
        if age > 300:
            raise HTTPException(401, "Session expired")
        
        if age >= 180:
            new_ts = now
            new_signed = signer.dumps(f"{user_id}.{new_ts}")
            response.set_cookie(
                "session_token",
                new_signed,
                httponly=True,
                max_age=300,
                secure=False
            )
        
        return {"user_id": user_id}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Invalid session")


@app.post("/login")
async def login(login_data: LoginRequest, response: Response):
    """Логин с динамическим продлением сессии (Задание 5.3)"""
    if login_data.username == "user123" and login_data.password == "password123":
        user_id = str(uuid.uuid4())
        now = int(time.time())
        data = f"{user_id}.{now}"
        signed = signer.dumps(data)
        response.set_cookie(
            key="session_token",
            value=signed,
            httponly=True,
            max_age=300,
            secure=False
        )
        return {"message": "Login successful", "user_id": user_id}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/profile")
async def profile(user=Depends(get_current_user), response: Response = None):
    """Профиль с динамическим продлением сессии (Задание 5.3)"""
    return {"message": f"Hello {user['user_id']}"}


# Задача 5.4
async def get_headers(
    user_agent: str = Header(..., description="User-Agent браузера"),
    accept_language: str = Header(..., description="Accept-Language заголовок")
):
    """Dependency для извлечения и валидации заголовков"""
    if not user_agent or not user_agent.strip():
        raise HTTPException(400, "User-Agent header is required")
    
    if not accept_language or not accept_language.strip():
        raise HTTPException(400, "Accept-Language header is required")
    
    pattern = r'^[a-zA-Z0-9\-_,;\s=qQ.*]+$'
    import re
    if not re.match(pattern, accept_language):
        raise HTTPException(400, "Invalid Accept-Language format")
    
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


@app.get("/headers")
async def get_headers_endpoint(headers: dict = Depends(get_headers)):
    """Возвращает заголовки запроса (Задание 5.4)"""
    return headers


# Задача 5.5
@app.get("/info")
async def info_endpoint(headers: dict = Depends(get_headers), response: Response = None):
    """Возвращает заголовки и информацию о сервере (Задание 5.4)"""
    response.headers["X-Server-Time"] = datetime.utcnow().isoformat()
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": headers
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
