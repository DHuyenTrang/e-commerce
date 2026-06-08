INSERT INTO shipments_carrier (id, code, name, is_active, config)
SELECT
  ('60000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'CAR_' || lpad(i::text, 2, '0'),
  'Carrier ' || lpad(i::text, 2, '0'),
  true,
  jsonb_build_object('mock', true, 'service_level', i)
FROM generate_series(1, 10) AS i
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, config = EXCLUDED.config;

INSERT INTO shipments_shippingrate (id, carrier_id, province, base_fee, fee_per_kg, estimated_days)
SELECT
  ('60000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('60000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Province ' || lpad(i::text, 2, '0'),
  18000 + i * 1000,
  4500 + i * 300,
  1 + (i % 5)
FROM generate_series(1, 10) AS i
ON CONFLICT (carrier_id, province) DO UPDATE SET base_fee = EXCLUDED.base_fee, fee_per_kg = EXCLUDED.fee_per_kg;

INSERT INTO shipments_shipment (
  id, order_id, carrier_id, tracking_number, status, shipping_fee, receiver_address_snapshot, created_at, updated_at
)
SELECT
  ('60000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('80000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('60000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'TRK' || lpad(i::text, 8, '0'),
  CASE WHEN i % 5 = 0 THEN 'CANCELLED' WHEN i % 5 = 1 THEN 'CREATED' WHEN i % 5 = 2 THEN 'IN_TRANSIT' WHEN i % 5 = 3 THEN 'DELIVERED' ELSE 'FAILED' END,
  25000 + i * 2000,
  jsonb_build_object('recipient_name', 'Customer ' || lpad(i::text, 2, '0'), 'province', 'Province ' || lpad(i::text, 2, '0')),
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (tracking_number) DO UPDATE SET status = EXCLUDED.status, updated_at = now();

INSERT INTO shipments_trackingevent (id, shipment_id, status, location, description, occurred_at)
SELECT
  ('60000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('60000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  'IN_TRANSIT',
  'Province ' || lpad(i::text, 2, '0'),
  'Mock tracking event ' || lpad(i::text, 2, '0'),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;
