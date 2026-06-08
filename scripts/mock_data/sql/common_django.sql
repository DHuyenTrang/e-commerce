INSERT INTO auth_user (
  id, password, last_login, is_superuser, username, first_name, last_name, email,
  is_staff, is_active, date_joined
)
SELECT
  9000 + i,
  '!mock-password',
  now() - (i || ' hours')::interval,
  false,
  'mock-user-' || lpad(i::text, 2, '0'),
  'Mock',
  'User ' || lpad(i::text, 2, '0'),
  'mock-user-' || lpad(i::text, 2, '0') || '@example.com',
  true,
  true,
  now() - (i || ' days')::interval
FROM generate_series(1, 10) AS i
ON CONFLICT (username) DO UPDATE SET
  email = EXCLUDED.email,
  is_active = EXCLUDED.is_active;

INSERT INTO auth_group (id, name)
SELECT 9000 + i, 'Mock Group ' || lpad(i::text, 2, '0')
FROM generate_series(1, 10) AS i
ON CONFLICT (name) DO NOTHING;

INSERT INTO auth_user_groups (id, user_id, group_id)
SELECT 9000 + i, 9000 + i, 9000 + i
FROM generate_series(1, 10) AS i
ON CONFLICT (user_id, group_id) DO NOTHING;

INSERT INTO auth_user_user_permissions (id, user_id, permission_id)
SELECT 9000 + row_number() OVER (), 9000 + row_number() OVER (), permission_id
FROM (
  SELECT id AS permission_id
  FROM auth_permission
  ORDER BY id
  LIMIT 10
) permissions
ON CONFLICT (user_id, permission_id) DO NOTHING;

INSERT INTO auth_group_permissions (id, group_id, permission_id)
SELECT 9000 + row_number() OVER (), 9000 + row_number() OVER (), permission_id
FROM (
  SELECT id AS permission_id
  FROM auth_permission
  ORDER BY id DESC
  LIMIT 10
) permissions
ON CONFLICT (group_id, permission_id) DO NOTHING;

INSERT INTO django_session (session_key, session_data, expire_date)
SELECT
  'mocksession' || lpad(i::text, 21, '0'),
  'e30:1mock:signature',
  now() + (30 + i || ' days')::interval
FROM generate_series(1, 10) AS i
ON CONFLICT (session_key) DO UPDATE SET
  session_data = EXCLUDED.session_data,
  expire_date = EXCLUDED.expire_date;

INSERT INTO django_admin_log (
  id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id
)
SELECT
  9000 + i,
  now() - (i || ' minutes')::interval,
  (9000 + i)::text,
  'Mock admin log ' || lpad(i::text, 2, '0'),
  1,
  'Seeded mock admin log',
  (SELECT id FROM django_content_type ORDER BY id LIMIT 1),
  9000 + i
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET
  change_message = EXCLUDED.change_message;
