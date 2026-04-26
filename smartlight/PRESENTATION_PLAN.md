# План видеодемонстрации — SmartLight Microservices

**Цель:** показать работу обоих микросервисов через Postman в соответствии с ТЗ.  
**Рекомендуемая длительность:** 8–12 минут.  
**Инструменты:** Postman, терминал с запущенным `docker compose`.

---

## Часть 1 — Запуск (1–2 мин)

1. Показать структуру папок в IDE/файловом менеджере — два сервиса, две БД, docker-compose.yml.
2. В терминале:
   ```bash
   docker compose up --build -d
   docker compose ps
   ```
3. Убедиться, что все 4 контейнера в статусе `healthy` / `running`.
4. Открыть в браузере Swagger UI обоих сервисов:
   - http://localhost:3001/docs
   - http://localhost:3002/docs

---

## Часть 2 — Catalog Service (3–4 мин)

> Импортировать `products_manage_postman.json` в Postman заранее.

### 2.1 Категории
- `GET /api/v1/categories`
- Показать ответ: 4 категории (LED, Filament, Smart, Halogen) с color_hex и sort_order.

### 2.2 Публичный каталог
- `GET /api/v1/products` — без фильтров, показать пагинацию в `meta`.
- `GET /api/v1/products?category=led` — фильтрация по категории.
- `GET /api/v1/products?category=led&limit=2&page=2` — вторая страница.
- `GET /api/v1/products/LX-LED-E27-9W` — карточка с атрибутами и изображениями.
- `GET /api/v1/products/NONEXISTENT` — показать **404** `product_not_found`.

### 2.3 Административные операции
- `POST /api/v1/products` — создать новый товар:
  ```json
  {
    "sku": "LX-TEST-001",
    "category_id": 1,
    "name": "Тестовая лампа",
    "price": 199.00,
    "stock_quantity": 10
  }
  ```
  Показать **201** с `id` и `created_at`.

- `POST /api/v1/products` с тем же SKU — показать **409** `sku_already_exists`.

- `PATCH /api/v1/products/LX-TEST-001`:
  ```json
  { "price": 249.00, "stock_quantity": 50 }
  ```
  Показать **200** с обновлёнными полями и новым `updated_at`.

- `DELETE /api/v1/products/LX-TEST-001` — **204 No Content**.
- Повторный `DELETE` — **404**.

---

## Часть 3 — Orders Service (4–5 мин)

> Импортировать `orders_manage_postman.json` в Postman заранее.  
> Добавить в коллекцию переменную `session_id` и заголовок `X-Session-Id: {{session_id}}` для всей папки Orders и Cart.

### 3.1 Корзина

- `GET /api/v1/cart` — пустая корзина, показать структуру ответа.

- `POST /api/v1/cart/items`:
  ```json
  { "sku": "LX-LED-E27-9W", "quantity": 2 }
  ```
  Показать **200**, `item_id`, `total_price = 178.00`.

- Добавить второй товар:
  ```json
  { "sku": "LX-SMT-E27-10W", "quantity": 1 }
  ```

- `GET /api/v1/cart` — показать оба товара, `subtotal`.

- `PATCH /api/v1/cart/items/1` — изменить количество первого товара:
  ```json
  { "quantity": 3 }
  ```

- `DELETE /api/v1/cart/items/2` — удалить второй товар.

- `GET /api/v1/cart` — убедиться, что остался один товар.

### 3.2 Оформление заказа

- `POST /api/v1/orders` — оформить заказ:
  ```json
  {
    "delivery_type": "courier",
    "delivery_city": "Москва",
    "delivery_street": "ул. Ленина, 1-42",
    "delivery_zip": "101000",
    "payment_method": "card_online"
  }
  ```
  Показать **201**: `order_number` вида `LX-YYYYMMDD-0001`, `delivery_cost: 300`, итоговая сумма.

- `GET /api/v1/cart` — показать, что корзина **очистилась автоматически**.

- Попытаться оформить заказ с пустой корзиной — **400** `cart_empty`.

### 3.3 Промокод (бонус)

- Добавить товар заново: `POST /api/v1/cart/items` с `LX-SMT-E27-10W`, qty 1 (цена 890).
- `POST /api/v1/orders` с `"promo_code": "SALE20"`:
  ```json
  {
    "delivery_type": "pickup",
    "payment_method": "card_online",
    "promo_code": "SALE20"
  }
  ```
  Показать `discount_amount` (−20% от 890 = 178), `delivery_cost: 0`, итог = 712.

### 3.4 История и детали

- `GET /api/v1/orders` — показать список двух созданных заказов с пагинацией.
- `GET /api/v1/orders/LX-...` — детали первого заказа: позиции, `status_history`.
- `GET /api/v1/orders/NONEXISTENT` — **404** `order_not_found`.

---

## Часть 4 — Завершение (30 сек)

- Показать `docker compose logs catalog-service` — видны SQL-запросы и 200-ответы.
- Закрыть словами: «Оба микросервиса реализованы, все эндпоинты из ТЗ покрыты».

---

## Советы по записи

- Включить в Postman вкладку **Pretty** для читаемого JSON.
- Использовать переменные Postman (`{{base_url}}`, `{{session_id}}`) — не копировать URL руками.
- Записывать экран в 1080p, шрифт терминала и Postman увеличить для читаемости.
- Комментировать каждое действие голосом: что отправляем и что ожидаем увидеть.
