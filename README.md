# E-Commerce Microservices

Hệ thống E-Commerce được thiết kế theo kiến trúc Microservices, sử dụng Django/Python cho các backend service và giao tiếp qua REST API thông qua API Gateway.

## Cấu trúc mục tiêu

Thiết kế tổng thể gồm 09 microservices theo bounded context:

- `user_service` - Customer Context
- `staff_service` - Staff Context
- `product_service` - Catalog Context
- `cart_service` - Cart Context
- `order_service` - Ordering Context
- `payment_service` - Payment Context
- `shipping_service` - Shipping Context
- `ai_service` - AI Service Context
- `comment_service` - Comment Context

Lưu ý: code scaffold hiện tại có thể chưa có đủ các service mục tiêu. Các service sẽ được cập nhật dần theo tài liệu thiết kế.

## Yêu cầu cài đặt

- Python 3.10+
- Docker và Docker Compose

## Chạy môi trường phát triển

### 1. Khởi chạy hạ tầng

```bash
docker-compose up -d
```

Docker Compose khởi chạy PostgreSQL, RabbitMQ và Redis phục vụ môi trường phát triển.

### 2. Kích hoạt Python environment

```powershell
.\venv\Scripts\Activate.ps1
pip install django djangorestframework psycopg2-binary
```

### 3. Chạy từng service

Mỗi service là một Django project độc lập. Ví dụ chạy Product Service:

```bash
cd product_service
python manage.py runserver 8002
```

## Tài liệu

- [Phân tích nghiệp vụ](docs/requirements.md)
- [Thiết kế hệ thống](docs/architecture.md)
- [Thiết kế User Service](docs/user_service_design.md)
- [Thiết kế Staff Service](docs/staff_service_design.md)
- [Thiết kế Product Service](docs/product_service_design.md)
- [Thiết kế Cart Service](docs/cart_service_design.md)
- [Thiết kế Order Service](docs/order_service_design.md)
- [Thiết kế Payment Service](docs/payment_service_design.md)
- [Thiết kế Shipping Service](docs/shipping_service_design.md)
- [Thiết kế AI Service](docs/ai_service_design.md)
- [Thiết kế Comment Service](docs/comment_service_design.md)
- [Thiết kế API Gateway](docs/api_gateway_design.md)
- [Thiết kế Front-end Service](docs/frontend_service_design.md)
