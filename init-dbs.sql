SELECT 'CREATE DATABASE gateway_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'gateway_db')\gexec
SELECT 'CREATE DATABASE user_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_db')\gexec
SELECT 'CREATE DATABASE staff_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'staff_db')\gexec
SELECT 'CREATE DATABASE product_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'product_db')\gexec
SELECT 'CREATE DATABASE cart_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cart_db')\gexec
SELECT 'CREATE DATABASE comment_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'comment_db')\gexec
SELECT 'CREATE DATABASE order_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'order_db')\gexec
SELECT 'CREATE DATABASE payment_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'payment_db')\gexec
SELECT 'CREATE DATABASE shipping_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'shipping_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE gateway_db TO root;
GRANT ALL PRIVILEGES ON DATABASE user_db TO root;
GRANT ALL PRIVILEGES ON DATABASE staff_db TO root;
GRANT ALL PRIVILEGES ON DATABASE product_db TO root;
GRANT ALL PRIVILEGES ON DATABASE cart_db TO root;
GRANT ALL PRIVILEGES ON DATABASE comment_db TO root;
GRANT ALL PRIVILEGES ON DATABASE order_db TO root;
GRANT ALL PRIVILEGES ON DATABASE payment_db TO root;
GRANT ALL PRIVILEGES ON DATABASE shipping_db TO root;
