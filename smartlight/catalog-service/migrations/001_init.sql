-- ============================================================
-- SmartLight — Catalog Service DB schema
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
  id         SERIAL PRIMARY KEY,
  slug       VARCHAR(50)  NOT NULL UNIQUE,
  name       VARCHAR(100) NOT NULL,
  color_hex  CHAR(7)      NOT NULL,
  sort_order SMALLINT     NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
  id             SERIAL PRIMARY KEY,
  sku            VARCHAR(50)   NOT NULL UNIQUE,
  category_id    INT           NOT NULL REFERENCES categories(id),
  name           VARCHAR(255)  NOT NULL,
  description    TEXT,
  price          NUMERIC(10,2) NOT NULL CHECK (price > 0),
  old_price      NUMERIC(10,2),
  stock_quantity INT           NOT NULL DEFAULT 0,
  status         VARCHAR(20)   NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active','archived','out_of_stock')),
  created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_attributes (
  id         SERIAL PRIMARY KEY,
  product_id INT          NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  attr_key   VARCHAR(50)  NOT NULL,
  attr_value VARCHAR(255) NOT NULL,
  unit       VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS product_images (
  id         SERIAL PRIMARY KEY,
  product_id INT          NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  url        TEXT         NOT NULL,
  alt_text   VARCHAR(255),
  is_primary BOOLEAN      NOT NULL DEFAULT FALSE,
  sort_order SMALLINT     NOT NULL DEFAULT 0
);

-- ============================================================
-- Seed data
-- ============================================================

INSERT INTO categories (slug, name, color_hex, sort_order) VALUES
  ('led',      'LED',      '#3B82F6', 0),
  ('filament', 'Filament', '#F59E0B', 1),
  ('smart',    'Smart',    '#10B981', 2),
  ('halogen',  'Halogen',  '#EF4444', 3)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO products (sku, category_id, name, description, price, old_price, stock_quantity, status) VALUES
  ('LX-LED-E27-9W',   1, 'Лампа светодиодная груша 9 Вт E27',
   'Энергосберегающая LED лампа с цоколем E27. Мощность 9 Вт заменяет лампу накаливания 75 Вт.',
   89.00, NULL, 150, 'active'),
  ('LX-LED-E14-7W',   1, 'Лампа светодиодная свеча 7 Вт E14',
   'Компактная LED лампа формы свечи. Идеальна для люстр и бра.',
   79.00, 99.00, 200, 'active'),
  ('LX-LED-GU10-5W',  1, 'Лампа светодиодная рефлектор 5 Вт GU10',
   'Направленная LED лампа с цоколем GU10 для точечных светильников.',
   119.00, NULL, 80, 'active'),
  ('LX-FIL-E27-4W',   2, 'Лампа филаментная 4 Вт E27',
   'Ретро-лампа с нитью накаливания. Создаёт уютное тёплое свечение.',
   299.00, NULL, 50, 'active'),
  ('LX-FIL-E27-6W',   2, 'Лампа филаментная 6 Вт E27',
   'Филаментная лампа повышенной яркости в форме шара.',
   349.00, 399.00, 35, 'active'),
  ('LX-SMT-E27-10W',  3, 'Умная лампа Smart 10 Вт E27',
   'Wi-Fi лампа с управлением со смартфона. Поддерживает 16 млн цветов и голосовые ассистенты.',
   890.00, NULL, 30, 'active'),
  ('LX-SMT-E14-9W',   3, 'Умная лампа Smart 9 Вт E14',
   'Компактная Smart-лампа с цоколем E14. Совместима с Яндекс Алиса и Google Home.',
   790.00, NULL, 25, 'active'),
  ('LX-HAL-GU10-50W', 4, 'Лампа галогенная рефлектор 50 Вт GU10',
   'Классическая галогенная лампа с цоколем GU10.',
   49.00, NULL, 0, 'out_of_stock')
ON CONFLICT (sku) DO NOTHING;

DO $$
DECLARE pid INT;
BEGIN
  SELECT id INTO pid FROM products WHERE sku = 'LX-LED-E27-9W';
  IF pid IS NOT NULL THEN
    INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
      (pid, 'wattage',    '9',     'Вт'),
      (pid, 'socket',     'E27',   NULL),
      (pid, 'lumens',     '806',   'лм'),
      (pid, 'color_temp', '4000',  'K'),
      (pid, 'lifespan',   '25000', 'ч');
    INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
      (pid, 'https://cdn.smartlight.ru/products/lx-led-e27-9w.jpg',   'Лампа LED E27 9Вт',              TRUE,  0),
      (pid, 'https://cdn.smartlight.ru/products/lx-led-e27-9w-2.jpg', 'Лампа LED E27 9Вт — вид сбоку', FALSE, 1);
  END IF;
END $$;

DO $$
DECLARE pid INT;
BEGIN
  SELECT id INTO pid FROM products WHERE sku = 'LX-SMT-E27-10W';
  IF pid IS NOT NULL THEN
    INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
      (pid, 'wattage', '10',  'Вт'),
      (pid, 'socket',  'E27', NULL),
      (pid, 'lumens',  '900', 'лм');
    INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
      (pid, 'https://cdn.smartlight.ru/products/lx-smt-e27-10w.jpg', 'Умная лампа Smart E27', TRUE, 0);
  END IF;
END $$;

-- ============================================================
-- Индексы
-- ============================================================

-- Основной поиск товаров — по категории и статусу
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_status       ON products(status);

-- Атрибуты и изображения всегда ищем по product_id
CREATE INDEX IF NOT EXISTS idx_product_attributes_product_id ON product_attributes(product_id);
CREATE INDEX IF NOT EXISTS idx_product_images_product_id     ON product_images(product_id);
