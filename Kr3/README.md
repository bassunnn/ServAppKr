# Kr3 - FastAPI Authentication & RBAC

Контрольная работа №3 — FastAPI с JWT аутентификацией, хешированием паролей, RBAC, rate limiting и SQLite.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Структура проекта

```
Kr3/
├── main.py            # Точка входа, инициализация приложения
├── security.py        # JWT, хеширование, rate limiting, зависимости
├── database.py        # SQLite CRUD операции
├── models.py          # Pydantic модели
├── config.py          # Переменные окружения (pydantic-settings)
├── routers/
│   ├── auth.py        # /auth/register, /auth/login
│   ├── todos.py       # CRUD для Todo
│   └── admin.py       # RBAC эндпоинты
├── .env               # Переменные окружения
└── requirements.txt   # Зависимости
```

## API Endpoints

### Аутентификация

| Метод | Путь | Описание | Rate Limit |
|-------|------|----------|------------|
| POST | `/auth/register` | Регистрация нового пользователя | 1/мин |
| POST | `/auth/login` | Вход, получение JWT токена | 5/мин |

### Todo (требуют JWT)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/todos/` | Создать Todo (201) |
| GET | `/todos/` | Получить все Todo |
| GET | `/todos/{id}` | Получить один Todo |
| PUT | `/todos/{id}` | Обновить Todo |
| DELETE | `/todos/{id}` | Удалить Todo |

### RBAC

| Метод | Путь | Роль | Описание |
|-------|------|------|----------|
| GET | `/public` | — | Публичный эндпоинт |
| GET | `/user-resource` | user/admin | Доступ для user и admin |
| GET | `/admin-resource` | admin | Только для admin |

### Документация (DEV режим)

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| GET | `/docs` | Basic | Swagger UI (защищено) |

## Тестирование (curl)

### 1. Регистрация
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass123"}'
```

### 2. Логин
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass123"}'
```

### 3. Создание Todo (с токеном)
```bash
curl -X POST http://127.0.0.1:8000/todos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"title":"Test","description":"My first todo"}'
```

### 4. RBAC — доступ для admin
```bash
# Зарегистрируйте пользователя "admin" — он получит роль admin
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}'

curl http://127.0.0.1:8000/admin-resource \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 5. Rate Limiting
Отправьте более 1 запроса на `/auth/register` за минуту — получите `429 Too Many Requests`.

## Роли

- `admin` — присваивается автоматически при username `admin`
- `user` — все остальные пользователи

## Коонфигурация (.env)

```env
MODE=DEV                    # DEV или PROD
DOCS_USER=docsadmin         # Логин для защиты /docs
DOCS_PASSWORD=docssecret    # Пароль для защиты /docs
SECRET_KEY=your-secret-key  # Секрет для JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

- **DEV** — `/docs` доступен с Basic Auth, `/redoc` отключён
- **PROD** — вся документация отключена (404)
