# E-Commerce Microservices

E-Commerce system built with Django microservices, an API Gateway, a React/Vite front end, and PostgreSQL for local development.

## Services

- `api_gateway` - routes `/api/v1/**` traffic to backend services.
- `user_service` - customer accounts and profiles.
- `staff_service` - staff accounts and RBAC.
- `product_service` - catalog and stock management.
- `cart_service` - guest and customer cart flows.
- `order_service` - order endpoints scaffold.
- `payment_service` - payment methods and transactions.
- `shipping_service` - shipping rates, shipments, tracking.
- `comment_service` - reviews, replies, moderation.
- `front-end` - customer storefront and admin portal.

## Run With Docker Compose

Docker Compose runs one shared `postgres:15-alpine` server with a separate database per service.

```powershell
docker compose up --build
```

Local ports:

- Front end: `http://localhost:5173`
- API Gateway: `http://localhost:8000`
- User: `http://localhost:8001`
- Staff: `http://localhost:8002`
- Product: `http://localhost:8003`
- Cart: `http://localhost:8004`
- Order: `http://localhost:8005`
- Payment: `http://localhost:8006`
- Shipping: `http://localhost:8007`
- Comment: `http://localhost:8009`
- PostgreSQL: `localhost:5432`

## Local Python Checks

The Django settings fall back to SQLite when PostgreSQL env vars are not set.

```powershell
python api_gateway\manage.py check
python user_service\manage.py check
python staff_service\manage.py check
python product_service\manage.py check
python cart_service\manage.py check
python order_service\manage.py check
python payment_service\manage.py check
python shipping_service\manage.py check
python comment_service\manage.py check
```

## Front End

```powershell
cd front-end
npm install
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm run dev
```

## Documentation

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API Gateway Design](docs/api_gateway_design.md)
- [Front-end Service Design](docs/frontend_service_design.md)
