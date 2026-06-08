INSERT INTO staff_core_department (id, code, name, description, status, created_at, updated_at)
SELECT
  ('20000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'DEPT_' || lpad(i::text, 2, '0'),
  'Department ' || lpad(i::text, 2, '0'),
  'Mock department ' || lpad(i::text, 2, '0'),
  'ACTIVE',
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, updated_at = now();

INSERT INTO staff_core_permission (id, code, resource, action, description, created_at)
SELECT
  ('20000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  'mock:permission:' || lpad(i::text, 2, '0'),
  'resource_' || lpad(i::text, 2, '0'),
  'manage',
  'Mock permission ' || lpad(i::text, 2, '0'),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description;

INSERT INTO staff_core_role (id, code, name, description, is_system_role, created_at, updated_at)
SELECT
  ('20000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  'ROLE_' || lpad(i::text, 2, '0'),
  'Role ' || lpad(i::text, 2, '0'),
  'Mock role ' || lpad(i::text, 2, '0'),
  i <= 3,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, updated_at = now();

INSERT INTO staff_core_staffaccount (
  id, employee_code, email, full_name, phone, department_id, status, last_login_at, created_at, updated_at
)
SELECT
  ('20000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  'EMP' || lpad(i::text, 4, '0'),
  'staff' || lpad(i::text, 2, '0') || '@example.com',
  'Staff Member ' || lpad(i::text, 2, '0'),
  '091000' || lpad(i::text, 4, '0'),
  ('20000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  'ACTIVE',
  now() - (i || ' hours')::interval,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (employee_code) DO UPDATE SET full_name = EXCLUDED.full_name, updated_at = now();

INSERT INTO staff_core_rolepermission (id, role_id, permission_id)
SELECT
  ('20000000-0000-0004-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('20000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('20000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid
FROM generate_series(1, 10) AS i
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO staff_core_staffrole (id, staff_id, role_id, assigned_at, assigned_by)
SELECT
  ('20000000-0000-0005-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('20000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('20000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  now(),
  ('20000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid
FROM generate_series(1, 10) AS i
ON CONFLICT (staff_id, role_id) DO NOTHING;
