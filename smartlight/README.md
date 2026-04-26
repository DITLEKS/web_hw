# SmartLight (Python / FastAPI)

Микросервисы реализованы на базе **Python 3.12 + FastAPI + asyncpg + PostgreSQL**.

| Сервис | Порт | БД |
|---|---|---|
| `catalog-service` | 3001 | `catalog_db` (PostgreSQL, порт 5433) |
| `orders-service`  | 3002 | `orders_db`  (PostgreSQL, порт 5434) |

Интерактивная документация (Swagger UI) доступна сразу после запуска:
- http://localhost:3001/docs
- http://localhost:3002/docs

---

## Быстрый старт (Docker Compose)

```bash
cd smartlight
docker compose up --build -d

# Проверить статус
docker compose ps

# Логи конкретного сервиса
docker compose logs -f catalog-service
docker compose logs -f orders-service
```

---

## Локальный запуск (без Docker)

### Требования
- Python 3.12+
- PostgreSQL 15+
- pip

### Catalog Service

```bash
cd catalog-service

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

createdb catalog_db
psql catalog_db < migrations/001_init.sql

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/catalog_db \
uvicorn app.main:app --port 3001 --reload
```

### Orders Service

```bash
cd orders-service

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

createdb orders_db
psql orders_db < migrations/001_init.sql

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/orders_db \
CATALOG_SERVICE_URL=http://localhost:3001 \
uvicorn app.main:app --port 3002 --reload
```

---

## Структура проекта

```
smartlight/
├── docker-compose.yml
├── catalog-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── migrations/
│   │   └── 001_init.sql          # Схема БД + seed-данные
│   └── app/
│       ├── main.py               # FastAPI-приложение, lifespan, роутеры
│       ├── database.py           # asyncpg pool, pydantic-settings
│       └── routers/
│           ├── categories.py     # GET /api/v1/categories
│           └── products.py       # CRUD /api/v1/products
└── orders-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── migrations/
    │   └── 001_init.sql          # Схема БД + промокоды
    └── app/
        ├── main.py
        ├── database.py           # asyncpg pool + httpx клиент для catalog
        └── routers/
            ├── cart.py           # Корзина (сессионная)
            └── orders.py         # Заказы
```

---

## API

### Catalog Service (порт 3001)

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/v1/categories` | Список категорий |
| GET | `/api/v1/products` | Каталог (`?category=led&page=1&limit=12&status=active`) |
| GET | `/api/v1/products/{sku}` | Карточка товара с атрибутами и изображениями |
| POST | `/api/v1/products` | Создать товар (admin) |
| PATCH | `/api/v1/products/{sku}` | Частично обновить товар (admin) |
| DELETE | `/api/v1/products/{sku}` | Удалить товар (admin) |

### Orders Service (порт 3002)

Корзина привязана к заголовку **`X-Session-Id`** (любой UUID).

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/v1/cart` | Содержимое корзины |
| POST | `/api/v1/cart/items` | Добавить товар `{ "sku": "...", "quantity": 2 }` |
| PATCH | `/api/v1/cart/items/{item_id}` | Изменить количество `{ "quantity": 3 }` |
| DELETE | `/api/v1/cart/items/{item_id}` | Удалить позицию |
| POST | `/api/v1/orders` | Оформить заказ |
| GET | `/api/v1/orders` | История заказов (`?page=1&limit=10`) |
| GET | `/api/v1/orders/{order_number}` | Детали заказа |

**Пример тела `POST /api/v1/orders`:**
```json
{
  "delivery_type": "courier",
  "delivery_city": "Москва",
  "delivery_street": "ул. Ленина, 1-42",
  "delivery_zip": "101000",
  "payment_method": "card_online",
  "promo_code": "SALE20"
}



