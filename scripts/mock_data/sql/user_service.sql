INSERT INTO accounts_useraccount (
  id, email, phone, password_hash, status, last_login_at, created_at, updated_at
)
SELECT
  ('10000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'customer' || lpad(i::text, 2, '0') || '@example.com',
  '090000' || lpad(i::text, 4, '0'),
  'pbkdf2_sha256$1000000$mock$mockhash',
  'ACTIVE',
  now() - (i || ' days')::interval,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (email) DO UPDATE SET
  phone = EXCLUDED.phone,
  status = EXCLUDED.status,
  updated_at = now();

INSERT INTO accounts_customerprofile (
  id, user_id, full_name, avatar_url, date_of_birth, gender, created_at, updated_at
)
SELECT
  ('10000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('10000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Customer ' || lpad(i::text, 2, '0'),
  'https://example.com/avatars/customer-' || lpad(i::text, 2, '0') || '.png',
  date '1990-01-01' + i,
  CASE WHEN i % 4 = 0 THEN 'UNSPECIFIED' WHEN i % 4 = 1 THEN 'MALE' WHEN i % 4 = 2 THEN 'FEMALE' ELSE 'OTHER' END,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (user_id) DO UPDATE SET
  full_name = EXCLUDED.full_name,
  updated_at = now();

INSERT INTO accounts_address (
  id, user_id, recipient_name, recipient_phone, province, district, ward, detail,
  is_default, is_deleted, created_at, updated_at
)
SELECT
  ('10000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('10000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Customer ' || lpad(i::text, 2, '0'),
  '090000' || lpad(i::text, 4, '0'),
  'Province ' || lpad(i::text, 2, '0'),
  'District ' || lpad(i::text, 2, '0'),
  'Ward ' || lpad(i::text, 2, '0'),
  lpad(i::text, 2, '0') || ' Commerce Street',
  true,
  false,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET
  recipient_name = EXCLUDED.recipient_name,
  updated_at = now();

INSERT INTO accounts_usersession (
  id, user_id, refresh_token_hash, device_info, ip_address, expires_at, revoked_at, created_at
)
SELECT
  ('10000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('10000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'mock-refresh-token-' || lpad(i::text, 2, '0'),
  'Mock Browser ' || lpad(i::text, 2, '0'),
  ('10.0.0.' || i)::inet,
  now() + (30 + i || ' days')::interval,
  null,
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET
  expires_at = EXCLUDED.expires_at,
  revoked_at = null;
