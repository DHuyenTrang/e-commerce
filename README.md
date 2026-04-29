# E-Commerce Microservices

Hệ thống E-Commerce được xây dựng trên kiến trúc Microservices sử dụng Framework Django (Python) và giao tiếp thông qua REST API cùng Message Broker (RabbitMQ).

## Cấu trúc dự án
Dự án bao gồm 9 Microservices riêng biệt:
- `user_service`
- `product_service`
- `cart_service`
- `order_service`
- `inventory_service`
- `promotion_service`
- `payment_service`
- `shipping_service`
- `search_service`

Mỗi service được khởi tạo dưới dạng một project Django độc lập, có thể chạy và mở rộng (scale) riêng biệt.

## Yêu cầu cài đặt (Prerequisites)
- Python 3.10+
- Docker và Docker Compose

## Hướng dẫn chạy môi trường (Development Environment)

### 1. Khởi chạy cơ sở hạ tầng (Infrastructure)
Bao gồm PostgreSQL, RabbitMQ và Redis:
```bash
docker-compose up -d
```
Docker sẽ tự động khởi tạo các database riêng biệt (`user_db`, `product_db`,...) cho từng Microservice dựa trên file `init-dbs.sql`.

### 2. Thiết lập môi trường Python (Python Environment)
Kích hoạt virtual environment và cài đặt các thư viện cần thiết (nếu bạn chưa cài):
```bash
# Đối với Windows PowerShell
.\venv\Scripts\Activate.ps1

# Cài đặt thư viện chung
pip install django djangorestframework psycopg2-binary
```

### 3. Cấu hình và khởi chạy từng Service
Mỗi service là một dự án Django riêng biệt. Trong quá trình phát triển, bạn sẽ cần trỏ database trong `settings.py` của từng service về localhost port 5432 với username `root`, password `rootpassword` và tên database tương ứng.

Ví dụ, chạy Product Service:
```bash
cd product_service
python manage.py runserver 8002
```

## Tài liệu (Documentation)
Vui lòng tham khảo thư mục `docs/`:
- [Yêu cầu Nghiệp vụ (Business Requirements)](docs/requirements.md)
- [Thiết kế Kiến trúc (Architecture Design)](docs/architecture.md)
