from datetime import datetime, timedelta
from typing import Optional
import secrets
import time
import jwt
import bcrypt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from config import get_settings
import database

# Хеширование и проверка пароля через bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Сравниваем введённый пароль с хешем в базе
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(password: str) -> str:
    # Генерируем соль и хешируем пароль
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def safe_compare_strings(a: str, b: str) -> bool:
    # Безопасное сравнение строк (защита от timing-атак)
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


# Настройка HTTP Basic аутентификации для защиты /docs

http_basic_security = HTTPBasic(auto_error=False)


# Загрузка настроек из .env файла

settings = get_settings()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Создаём JWT токен с expiration
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Декодируем и проверяем JWT токен
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Токен просрочен
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        # Невалидный токен
        raise HTTPException(status_code=401, detail="Invalid token")


# In-memory rate limiter — считает запросы по IP и действию

class InMemoryRateLimiter:
    def __init__(self):
        self.requests: dict[str, list[float]] = {}

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []

        # Удаляем запросы старше окна
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]

        # Превышен лимит — блокируем
        if len(self.requests[key]) >= max_requests:
            return True

        # Записываем время запроса
        self.requests[key].append(now)
        return False


rate_limiter = InMemoryRateLimiter()


# Извлекаем username и role из Bearer токена

def get_current_user(request: Request) -> dict:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authentication scheme", headers={"WWW-Authenticate": "Bearer"})

    payload = decode_access_token(token)
    username = payload.get("sub")
    role = payload.get("role")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload", headers={"WWW-Authenticate": "Bearer"})

    return {"username": username, "role": role}


# Зависимость для проверки роли — возвращает 403 если роль не совпадает
def require_role(role: str):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return dependency


# Проверяем rate limit по IP и действию — возвращаем 429 при превышении
def check_rate_limit(request: Request, max_requests: int = 5, window_seconds: int = 60, action: str = "default"):
    client_ip = request.client.host
    key = f"{client_ip}:{action}"
    if rate_limiter.is_rate_limited(key, max_requests, window_seconds):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")


# Проверяем логин/пароль для доступа к /docs — защищаем Basic Auth
def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(http_basic_security)):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not (safe_compare_strings(credentials.username, settings.DOCS_USER) and
            safe_compare_strings(credentials.password, settings.DOCS_PASSWORD)):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
