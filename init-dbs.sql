CREATE DATABASE user_db;
CREATE DATABASE product_db;
CREATE DATABASE cart_db;
CREATE DATABASE order_db;
CREATE DATABASE inventory_db;
CREATE DATABASE promotion_db;
CREATE DATABASE payment_db;
CREATE DATABASE shipping_db;
CREATE DATABASE search_db;

-- Grant privileges (optional, assuming root user is used for simplicity in local dev)
GRANT ALL PRIVILEGES ON DATABASE user_db TO root;
GRANT ALL PRIVILEGES ON DATABASE product_db TO root;
GRANT ALL PRIVILEGES ON DATABASE cart_db TO root;
GRANT ALL PRIVILEGES ON DATABASE order_db TO root;
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO root;
GRANT ALL PRIVILEGES ON DATABASE promotion_db TO root;
GRANT ALL PRIVILEGES ON DATABASE payment_db TO root;
GRANT ALL PRIVILEGES ON DATABASE shipping_db TO root;
GRANT ALL PRIVILEGES ON DATABASE search_db TO root;
