-- ============================================================
-- Schema
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
-- Seed: Categories
-- ============================================================

INSERT INTO categories (slug, name, color_hex, sort_order) VALUES
  ('led',      'LED',      '#3B82F6', 0),
  ('filament', 'Filament', '#F59E0B', 1),
  ('smart',    'Smart',    '#10B981', 2),
  ('halogen',  'Halogen',  '#EF4444', 3)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- Seed: Products (12 товаров — полное соответствие фронт-моку)
-- ============================================================

INSERT INTO products (sku, category_id, name, description, price, old_price, stock_quantity, status) VALUES
  -- LED
  ('LX-LED-E27-9W',   1, 'Лампа светодиодная груша 9 Вт E27',
   'Энергосберегающая LED лампа с цоколем E27. Мощность 9 Вт заменяет лампу накаливания 75 Вт. Тёплый белый свет 4000K обеспечивает комфортное освещение для жилых помещений.',
   89.00, NULL, 150, 'active'),

  ('LX-LED-E14-7W',   1, 'Лампа светодиодная свеча 7 Вт E14',
   'Компактная LED лампа формы свечи с цоколем E14. Идеальна для люстр, бра и настольных ламп. Потребляет на 90% меньше энергии по сравнению с лампами накаливания той же яркости.',
   79.00, 99.00, 200, 'active'),

  ('LX-LED-GU10-5W',  1, 'Лампа светодиодная рефлектор 5 Вт GU10',
   'Направленная LED лампа с цоколем GU10 для точечных светильников и спотов. Угол рассеивания 36°. Подходит для акцентного освещения в кухнях, магазинах и офисах.',
   119.00, NULL, 80, 'active'),

  ('LX-LED-E27-12W',  1, 'Лампа светодиодная груша 12 Вт E27',
   'Мощная LED лампа для больших помещений. 1100 лм, нейтральный белый свет 4000K.',
   129.00, 159.00, 90, 'active'),

  -- Filament
  ('LX-FIL-E27-4W',   2, 'Лампа филаментная 4 Вт E27',
   'Ретро-лампа с видимой нитью накаливания в колбе шар. Создаёт тёплое уютное свечение 2200K. Незаменима для создания атмосферного освещения в ресторанах, кафе и жилых пространствах.',
   299.00, NULL, 50, 'active'),

  ('LX-FIL-E27-6W',   2, 'Лампа филаментная 6 Вт E27',
   'Филаментная лампа повышенной яркости в форме вытянутого эллипса (ST64). Декоративная нить Edison создаёт атмосферное освещение. Диммируется большинством диммеров.',
   349.00, 399.00, 35, 'active'),

  ('LX-FIL-E14-4W',   2, 'Лампа филаментная свеча 4 Вт E14',
   'Филаментная лампа форм-фактора свеча с цоколем E14. Идеальна для хрустальных люстр.',
   249.00, NULL, 40, 'active'),

  -- Smart
  ('LX-SMT-E27-10W',  3, 'Умная лампа Smart 10 Вт E27',
   'Wi-Fi лампа с управлением через смартфон или голосовой ассистент. Поддерживает 16 миллионов цветов, регулировку яркости и тёплой/холодной температуры.',
   890.00, NULL, 30, 'active'),

  ('LX-SMT-E14-9W',   3, 'Умная лампа Smart 9 Вт E14',
   'Компактная Smart-лампа с цоколем E14 для малых светильников. Полный набор функций: цвет, яркость, расписания, сценарии.',
   790.00, NULL, 25, 'active'),

  ('LX-SMT-GU10-6W',  3, 'Умная лампа GU10 6 Вт RGB',
   'Умная лампа с цоколем GU10, поддержкой RGB и управлением через приложение. 16 млн цветов.',
   590.00, 690.00, 20, 'active'),

  -- Halogen
  ('LX-HAL-GU10-50W', 4, 'Лампа галогенная рефлектор 50 Вт GU10',
   'Классическая галогенная лампа с цоколем GU10. Идеальная цветопередача (CRI 100), мгновенный розжиг.',
   49.00, NULL, 0, 'out_of_stock'),

  ('LX-HAL-E27-42W',  4, 'Лампа галогенная груша 42 Вт E27',
   'Классическая галогенная лампа с улучшенной цветопередачей. Замена 60 Вт лампы накаливания.',
   65.00, NULL, 0, 'out_of_stock')

ON CONFLICT (sku) DO UPDATE SET
  name           = EXCLUDED.name,
  description    = EXCLUDED.description,
  price          = EXCLUDED.price,
  old_price      = EXCLUDED.old_price,
  stock_quantity = EXCLUDED.stock_quantity,
  status         = EXCLUDED.status,
  updated_at     = NOW();

-- ============================================================
-- Seed: Attributes & Images (все 12 товаров)
-- ============================================================

DO $$
DECLARE pid INT;
BEGIN
  -- LX-LED-E27-9W
  SELECT id INTO pid FROM products WHERE sku = 'LX-LED-E27-9W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','9','Вт'),(pid,'socket','E27',NULL),(pid,'lumens','806','лм'),
    (pid,'color_temp','4000','K'),(pid,'lifespan','25000','ч');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/led-e27-9w.jpg','Лампа LED E27 9Вт',TRUE,0);

  -- LX-LED-E14-7W
  SELECT id INTO pid FROM products WHERE sku = 'LX-LED-E14-7W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','7','Вт'),(pid,'socket','E14',NULL),(pid,'lumens','630','лм'),
    (pid,'color_temp','2700','K'),(pid,'lifespan','25000','ч');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/led-e14-7w.jpg','LED свеча E14',TRUE,0);

  -- LX-LED-GU10-5W
  SELECT id INTO pid FROM products WHERE sku = 'LX-LED-GU10-5W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','5','Вт'),(pid,'socket','GU10',NULL),(pid,'lumens','400','лм'),
    (pid,'color_temp','3000','K'),(pid,'angle','36','°');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/led-gu10-5w.jpg','LED GU10 5Вт',TRUE,0);

  -- LX-LED-E27-12W
  SELECT id INTO pid FROM products WHERE sku = 'LX-LED-E27-12W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','12','Вт'),(pid,'socket','E27',NULL),(pid,'lumens','1100','лм'),
    (pid,'color_temp','4000','K'),(pid,'lifespan','25000','ч');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/led-e27-12w.jpg','LED E27 12Вт',TRUE,0);

  -- LX-FIL-E27-4W
  SELECT id INTO pid FROM products WHERE sku = 'LX-FIL-E27-4W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','4','Вт'),(pid,'socket','E27',NULL),(pid,'lumens','300','лм'),
    (pid,'color_temp','2200','K'),(pid,'lifespan','15000','ч');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/fil-e27-4w.jpg','Филаментная лампа E27',TRUE,0);

  -- LX-FIL-E27-6W
  SELECT id INTO pid FROM products WHERE sku = 'LX-FIL-E27-6W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','6','Вт'),(pid,'socket','E27',NULL),(pid,'lumens','500','лм'),
    (pid,'color_temp','2200','K'),(pid,'lifespan','15000','ч');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/fil-e27-6w.jpg','Филаментная ST64 E27',TRUE,0);

  -- LX-FIL-E14-4W
  SELECT id INTO pid FROM products WHERE sku = 'LX-FIL-E14-4W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','4','Вт'),(pid,'socket','E14',NULL),(pid,'lumens','270','лм'),
    (pid,'color_temp','2200','K'),(pid,'lifespan','15000','ч');
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/fil-e14-4w.jpg','Филаментная свеча E14',TRUE,0);

  -- LX-SMT-E27-10W
  SELECT id INTO pid FROM products WHERE sku = 'LX-SMT-E27-10W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','10','Вт'),(pid,'socket','E27',NULL),(pid,'lumens','900','лм'),
    (pid,'color_temp','2700-6500','K'),(pid,'wifi','2.4GHz',NULL);
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/smt-e27-10w.jpg','Умная лампа E27 RGB',TRUE,0);

  -- LX-SMT-E14-9W
  SELECT id INTO pid FROM products WHERE sku = 'LX-SMT-E14-9W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','9','Вт'),(pid,'socket','E14',NULL),(pid,'lumens','800','лм'),
    (pid,'color_temp','2700-6500','K'),(pid,'wifi','2.4GHz',NULL);
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/smt-e14-9w.jpg','Умная лампа E14',TRUE,0);

  -- LX-SMT-GU10-6W
  SELECT id INTO pid FROM products WHERE sku = 'LX-SMT-GU10-6W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','6','Вт'),(pid,'socket','GU10',NULL),(pid,'lumens','500','лм'),
    (pid,'color_temp','RGB',NULL),(pid,'wifi','2.4GHz',NULL);
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/smt-gu10-6w.jpg','Умная лампа GU10 RGB',TRUE,0);

  -- LX-HAL-GU10-50W
  SELECT id INTO pid FROM products WHERE sku = 'LX-HAL-GU10-50W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','50','Вт'),(pid,'socket','GU10',NULL),(pid,'lumens','700','лм'),
    (pid,'color_temp','3000','K'),(pid,'cri','100',NULL);
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/hal-gu10-50w.jpg','Галогенная GU10 50Вт',TRUE,0);

  -- LX-HAL-E27-42W
  SELECT id INTO pid FROM products WHERE sku = 'LX-HAL-E27-42W';
  DELETE FROM product_attributes WHERE product_id = pid;
  DELETE FROM product_images     WHERE product_id = pid;
  INSERT INTO product_attributes (product_id, attr_key, attr_value, unit) VALUES
    (pid,'wattage','42','Вт'),(pid,'socket','E27',NULL),(pid,'lumens','630','лм'),
    (pid,'color_temp','3000','K'),(pid,'cri','100',NULL);
  INSERT INTO product_images (product_id, url, alt_text, is_primary, sort_order) VALUES
    (pid,'/images/hal-e27-42w.jpg','Галогенная груша E27',TRUE,0);

END $$;

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_products_category_id          ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_status               ON products(status);
CREATE INDEX IF NOT EXISTS idx_product_attributes_product_id ON product_attributes(product_id);
CREATE INDEX IF NOT EXISTS idx_product_images_product_id     ON product_images(product_id);
