INSERT INTO payments_paymentmethod (id, code, name, provider, is_active, config)
SELECT
  ('50000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'PAY_' || lpad(i::text, 2, '0'),
  'Payment Method ' || lpad(i::text, 2, '0'),
  CASE WHEN i % 5 = 0 THEN 'cod' WHEN i % 5 = 1 THEN 'momo' WHEN i % 5 = 2 THEN 'vnpay' WHEN i % 5 = 3 THEN 'stripe' ELSE 'zalopay' END,
  true,
  jsonb_build_object('mock', true, 'priority', i)
FROM generate_series(1, 10) AS i
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, config = EXCLUDED.config;

INSERT INTO payments_paymenttransaction (
  id, order_id, transaction_code, amount, currency, payment_method_id, status,
  gateway_reference, paid_at, failure_reason, created_at, updated_at
)
SELECT
  ('50000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('80000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'TXN-' || lpad(i::text, 6, '0'),
  150000 + i * 25000,
  'VND',
  ('50000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  CASE WHEN i % 4 = 0 THEN 'CANCELLED' WHEN i % 4 = 1 THEN 'PENDING' WHEN i % 4 = 2 THEN 'SUCCESS' ELSE 'FAILED' END,
  'GW-REF-' || lpad(i::text, 6, '0'),
  CASE WHEN i % 2 = 0 THEN now() - (i || ' days')::interval ELSE null END,
  CASE WHEN i % 3 = 0 THEN 'Mock failure reason' ELSE '' END,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (transaction_code) DO UPDATE SET status = EXCLUDED.status, updated_at = now();

INSERT INTO payments_paymentgatewaycallback (id, transaction_id, provider, payload, signature_valid, received_at)
SELECT
  ('50000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('50000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  'mock-provider',
  jsonb_build_object('transaction_code', 'TXN-' || lpad(i::text, 6, '0'), 'mock', true),
  i % 2 = 0,
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload;
