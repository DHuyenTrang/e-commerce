INSERT INTO catalog_category (id, parent_id, name, slug, description, status, created_at, updated_at)
SELECT
  ('30000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  null,
  'Category ' || lpad(i::text, 2, '0'),
  'category-' || lpad(i::text, 2, '0'),
  'Mock category ' || lpad(i::text, 2, '0'),
  'ACTIVE',
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, updated_at = now();

INSERT INTO catalog_brand (id, name, slug, logo_url, description, status, created_at, updated_at)
SELECT
  ('30000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Brand ' || lpad(i::text, 2, '0'),
  'brand-' || lpad(i::text, 2, '0'),
  'https://example.com/brands/' || lpad(i::text, 2, '0') || '.png',
  'Mock brand ' || lpad(i::text, 2, '0'),
  'ACTIVE',
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, updated_at = now();

INSERT INTO catalog_tag (id, name, slug, status, created_at, updated_at)
SELECT
  ('30000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Tag ' || lpad(i::text, 2, '0'),
  'tag-' || lpad(i::text, 2, '0'),
  'ACTIVE',
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, updated_at = now();

INSERT INTO catalog_product (
  id, name, slug, sku, category_id, brand_id, price, original_price, stock_quantity,
  status, attributes, created_at, updated_at
)
SELECT
  ('30000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Mock Product ' || lpad(i::text, 2, '0'),
  'mock-product-' || lpad(i::text, 2, '0'),
  'MOCK-SKU-' || lpad(i::text, 4, '0'),
  ('30000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('30000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  99000 + i * 10000,
  129000 + i * 10000,
  50 + i,
  'ACTIVE',
  jsonb_build_object('mock', true, 'index', i),
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (sku) DO UPDATE SET price = EXCLUDED.price, updated_at = now();

INSERT INTO catalog_image (id, product_id, url, alt_text, sort_order, is_thumbnail)
SELECT
  ('30000000-0000-0004-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('30000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  'https://picsum.photos/seed/mock-product-' || lpad(i::text, 2, '0') || '/800/600',
  'Mock Product ' || lpad(i::text, 2, '0'),
  0,
  true
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url;

INSERT INTO catalog_producttag (id, product_id, tag_id)
SELECT
  ('30000000-0000-0005-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('30000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('30000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid
FROM generate_series(1, 10) AS i
ON CONFLICT (product_id, tag_id) DO NOTHING;
