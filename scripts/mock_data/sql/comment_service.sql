INSERT INTO comments_review (
  id, product_id, user_id, order_id, rating, content, status, created_at, updated_at
)
SELECT
  ('70000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('30000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('10000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('80000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  1 + (i % 5),
  'Mock review content ' || lpad(i::text, 2, '0'),
  CASE WHEN i % 3 = 0 THEN 'HIDDEN' ELSE 'VISIBLE' END,
  now(),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, updated_at = now();

INSERT INTO comments_commentreply (id, review_id, staff_id, content, status, created_at)
SELECT
  ('70000000-0000-0001-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('70000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  ('20000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Mock reply ' || lpad(i::text, 2, '0'),
  'VISIBLE',
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content;

INSERT INTO comments_commentmoderation (
  id, target_type, target_id, action, moderated_by, reason, created_at
)
SELECT
  ('70000000-0000-0002-0000-' || lpad(i::text, 12, '0'))::uuid,
  'review',
  ('70000000-0000-0000-0000-' || lpad(i::text, 12, '0'))::uuid,
  CASE WHEN i % 3 = 0 THEN 'HIDE' ELSE 'SHOW' END,
  ('20000000-0000-0003-0000-' || lpad(i::text, 12, '0'))::uuid,
  'Mock moderation reason ' || lpad(i::text, 2, '0'),
  now()
FROM generate_series(1, 10) AS i
ON CONFLICT (id) DO UPDATE SET reason = EXCLUDED.reason;
