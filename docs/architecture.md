# Kiến trúc hệ thống E-Commerce Microservices

Hệ thống được thiết kế theo kiến trúc Microservices, giao tiếp với nhau thông qua API Gateway (Synchronous) và Message Broker (Asynchronous). Toàn bộ hệ thống được xây dựng bằng framework Django và cơ sở dữ liệu PostgreSQL.

## 1. Biểu đồ Kiến trúc (Architecture Diagram)

```mermaid
graph TD
    Client[Client Apps (Web/Mobile)] --> Gateway[API Gateway (Nginx/Kong)]
    
    subgraph Microservices [Django Microservices]
        User[User Service]
        Product[Product Service]
        Cart[Cart Service]
        Order[Order Service]
        Payment[Payment Service]
        Shipping[Shipping Service]
        Inventory[Inventory Service]
        Promotion[Promotion Service]
        Search[Search Service]
    end

    Gateway --> User
    Gateway --> Product
    Gateway --> Cart
    Gateway --> Order
    Gateway --> Search

    %% Asynchronous Communication via Message Broker
    Broker((Message Broker - RabbitMQ))

    Order -- "Publish Event (OrderCreated)" --> Broker
    Payment -- "Publish Event (PaymentSuccess)" --> Broker
    Shipping -- "Publish Event (ShippingUpdated)" --> Broker
    Product -- "Publish Event (ProductUpdated)" --> Broker

    Broker -. "Consume" .-> Inventory
    Broker -. "Consume" .-> Shipping
    Broker -. "Consume" .-> Payment
    Broker -. "Consume" .-> Promotion
    Broker -. "Consume" .-> Search
    Broker -. "Consume" .-> Order

    %% Databases
    DB_User[(PostgreSQL: User)] --- User
    DB_Product[(PostgreSQL: Product)] --- Product
    DB_Cart[(PostgreSQL: Cart)] --- Cart
    DB_Order[(PostgreSQL: Order)] --- Order
    DB_Inventory[(PostgreSQL: Inventory)] --- Inventory
    DB_Promotion[(PostgreSQL: Promotion)] --- Promotion
    DB_Payment[(PostgreSQL: Payment)] --- Payment
    DB_Shipping[(PostgreSQL: Shipping)] --- Shipping
```

## 2. Thiết kế Cơ sở dữ liệu (Database Design)

Mỗi service sẽ có một database (hoặc schema) riêng biệt trong PostgreSQL để đảm bảo tính độc lập dữ liệu theo chuẩn Microservices.

*   **Product Service:** Sử dụng kiểu dữ liệu `JSONB` của PostgreSQL để lưu trữ cấu hình sản phẩm linh hoạt (thông số kỹ thuật đồ điện tử, thông tin sách, size/màu sắc thời trang).
*   **Transaction:** Với hệ thống phân tán, các giao dịch liên dịch vụ (như tạo Order, trừ Inventory, thanh toán Payment) sẽ được xử lý qua mô hình **Saga Pattern** hoặc **2PC**, kết hợp với Message Broker.

## 3. Cơ chế giao tiếp (Communication Strategy)

*   **Synchronous (HTTP/REST):** Dành cho thao tác truy vấn trực tiếp từ phía người dùng (thông qua Gateway) và những lời gọi API yêu cầu đồng bộ ngay lập tức.
*   **Asynchronous (Event-Driven / Message Queue):** Sử dụng **RabbitMQ**. Các service phát (publish) event khi có thay đổi trạng thái, các service khác đăng ký (subscribe) để phản hồi:
    *   *Ví dụ 1:* Khi `Order Service` nhận được yêu cầu tạo đơn hàng -> tạo trạng thái *Pending* và phát sự kiện `OrderCreated`. `Inventory Service` lắng nghe để khóa tồn kho. Nếu thành công, phản hồi lại Order Service để tiếp tục; nếu thất bại (hết hàng), Order Service chuyển trạng thái đơn hàng thành *Cancelled*.
    *   *Ví dụ 2:* Khi `Payment Service` thanh toán thành công -> phát sự kiện `PaymentSucceeded`. `Order Service` cập nhật trạng thái đơn hàng và `Shipping Service` bắt đầu tạo vận đơn.

## 4. Công nghệ sử dụng (Tech Stack)

*   **Backend:** Python 3.x, Django, Django REST Framework (DRF)
*   **Database:** PostgreSQL 15+
*   **Message Broker:** RabbitMQ
*   **Background Tasks:** Celery + Redis (làm Celery Broker hoặc Result Backend)
*   **Containerization:** Docker & Docker Compose
