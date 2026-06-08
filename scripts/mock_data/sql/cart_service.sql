INSERT INTO cart_core_cart (id, user_id, guest_session_id, status, created_at, updated_at)
SELECT
  ('40000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('10000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'guest-session-' || lpad(i::text, 2, '0'),
  'ACTIVE',
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, updated_at = now();

INSERT INTO cart_core_cartitem (id, cart_id, product_id, sku, quantity, added_at, updated_at)
SELECT
  ('40000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('40000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('30000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  'MOCK-SKU-' || lpad(i::text, 4, '0'),
  i,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (cart_id, product_id, sku) DO UPDATE SET quantity = EXCLUDED.quantity, updated_at = now();
