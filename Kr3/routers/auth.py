from fastapi import APIRouter, HTTPException, Request
from models import UserRegister, UserLogin, TokenResponse
import database
from security import check_rate_limit, hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201, response_model=dict)
async def register(request: Request, user: UserRegister):
    # Rate limiting: 1 запрос в минуту
    check_rate_limit(request, max_requests=1, window_seconds=60, action="register")

    # Проверяем, существует ли пользователь
    existing_user = database.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    # Хешируем пароль
    hashed_password = hash_password(user.password)

    # Определяем роль
    role = "admin" if user.username == "admin" else "user"

    # Создаём пользователя
    result = database.create_user(user.username, hashed_password, role)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create user")

    return {"message": "New user created"}


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, user: UserLogin):
    # Rate limiting: 5 запросов в минуту
    check_rate_limit(request, max_requests=5, window_seconds=60, action="login")

    # Ищем пользователя
    db_user = database.get_user_by_username(user.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем пароль
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Создаём токен
    access_token = create_access_token(
        data={"sub": db_user["username"], "role": db_user["role"]}
    )

    return {"access_token": access_token, "token_type": "bearer"}
