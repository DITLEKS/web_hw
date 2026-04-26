-- ============================================================
-- SmartLight — Orders Service DB schema
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
  id             SERIAL PRIMARY KEY,
  email          VARCHAR(254) NOT NULL UNIQUE,
  first_name     VARCHAR(100) NOT NULL,
  last_name      VARCHAR(100) NOT NULL,
  phone          VARCHAR(20),
  password_hash  VARCHAR(60),
  email_verified BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS promo_codes (
  id               SERIAL PRIMARY KEY,
  code             VARCHAR(50)   NOT NULL UNIQUE,
  discount_type    VARCHAR(10)   NOT NULL CHECK (discount_type IN ('percent','fixed')),
  discount_value   NUMERIC(10,2) NOT NULL,
  min_order_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
  max_uses         INT,
  used_count       INT           NOT NULL DEFAULT 0,
  valid_from       TIMESTAMPTZ   NOT NULL,
  valid_until      TIMESTAMPTZ,
  is_active        BOOLEAN       NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS orders (
  id               SERIAL PRIMARY KEY,
  order_number     VARCHAR(30)   NOT NULL UNIQUE,
  customer_id      INT           REFERENCES customers(id),
  status           VARCHAR(30)   NOT NULL DEFAULT 'created'
                     CHECK (status IN ('created','confirmed','in_assembly','shipped','delivered','cancelled')),
  delivery_type    VARCHAR(20)   NOT NULL CHECK (delivery_type IN ('courier','pickup','cdek')),
  delivery_city    VARCHAR(100),
  delivery_street  VARCHAR(255),
  delivery_zip     VARCHAR(10),
  promo_code_id    INT           REFERENCES promo_codes(id),
  discount_amount  NUMERIC(10,2) NOT NULL DEFAULT 0,
  subtotal         NUMERIC(10,2) NOT NULL,
  delivery_cost    NUMERIC(10,2) NOT NULL DEFAULT 0,
  total_amount     NUMERIC(10,2) NOT NULL,
  payment_method   VARCHAR(20)   NOT NULL
                     CHECK (payment_method IN ('card_online','cash_on_delivery','card_on_delivery')),
  payment_status   VARCHAR(20)   NOT NULL DEFAULT 'pending'
                     CHECK (payment_status IN ('pending','paid','refunded','failed')),
  tracking_number  VARCHAR(100),
  operator_comment TEXT,
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
  id          SERIAL PRIMARY KEY,
  order_id    INT           NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  sku         VARCHAR(50)   NOT NULL,
  name        VARCHAR(255)  NOT NULL,
  quantity    SMALLINT      NOT NULL CHECK (quantity > 0),
  unit_price  NUMERIC(10,2) NOT NULL,
  total_price NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_status_history (
  id         SERIAL PRIMARY KEY,
  order_id   INT          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  old_status VARCHAR(30),
  new_status VARCHAR(30)  NOT NULL,
  changed_by VARCHAR(254) NOT NULL DEFAULT 'system',
  comment    TEXT,
  changed_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
  id          SERIAL PRIMARY KEY,
  session_id  VARCHAR(64)   NOT NULL,
  sku         VARCHAR(50)   NOT NULL,
  name        VARCHAR(255)  NOT NULL,
  unit_price  NUMERIC(10,2) NOT NULL,
  quantity    SMALLINT      NOT NULL CHECK (quantity > 0),
  total_price NUMERIC(10,2) NOT NULL,
  added_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, sku)
);

-- ============================================================
-- Seed promo codes
-- ============================================================

INSERT INTO promo_codes (code, discount_type, discount_value, min_order_amount, max_uses, valid_from, valid_until, is_active) VALUES
  ('SALE20',  'percent', 20.00,  500.00,  NULL, '2026-01-01', '2026-12-31', TRUE),
  ('WELCOME', 'fixed',   150.00, 0.00,    1000, '2026-01-01', '2026-12-31', TRUE),
  ('SMART15', 'percent', 15.00,  1000.00, NULL, '2026-01-01', '2026-06-30', TRUE)
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- Индексы
-- ============================================================

-- Корзина всегда ищется по session_id
CREATE INDEX IF NOT EXISTS idx_cart_items_session_id ON cart_items(session_id);

-- История заказов — сортировка по дате, поиск по статусу
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status     ON orders(status);

-- Позиции и история — всегда по order_id
CREATE INDEX IF NOT EXISTS idx_order_items_order_id          ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id ON order_status_history(order_id);
