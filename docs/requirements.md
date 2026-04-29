# Yêu cầu Nghiệp vụ (Business Requirements) - E-commerce Microservices

## 1. Tổng quan hệ thống (System Overview)
Hệ thống thương mại điện tử đa ngành hàng (sách, đồ điện tử, thời trang) dựa trên kiến trúc Microservices, đảm bảo tính mở rộng, tính sẵn sàng cao và dễ dàng bảo trì.

## 2. Các chức năng cốt lõi (Core Features)

### 2.1 Quản lý người dùng (User Management Service)
*   **Roles:** Admin, Staff, Customer.
*   **Customer:** Đăng ký, đăng nhập, quản lý hồ sơ cá nhân, quản lý địa chỉ nhận hàng, xem lịch sử mua hàng.
*   **Staff:** Quản lý sản phẩm, xử lý đơn hàng, hỗ trợ khách hàng.
*   **Admin:** Quản lý toàn bộ hệ thống, phân quyền, xem báo cáo doanh thu, quản lý nhân viên.
*   **Security:** Xác thực và phân quyền dựa trên JWT, Role-based Access Control (RBAC).

### 2.2 Quản lý sản phẩm (Product Catalog Service)
Hỗ trợ đa ngành hàng (multi-domain). Mỗi ngành hàng sẽ có các thuộc tính đặc thù:
*   **Sách (Book):** Tác giả, nhà xuất bản, năm xuất bản, số trang, ISBN.
*   **Đồ điện tử (Electronics):** Thương hiệu, thông số kỹ thuật (RAM, ROM, CPU, v.v.), thời gian bảo hành.
*   **Thời trang (Fashion):** Kích cỡ (Size), màu sắc, chất liệu, giới tính.
*   **Chức năng chung:** Quản lý danh mục (Category), giá cả, hình ảnh, mô tả sản phẩm, đánh giá/nhận xét (Review).

### 2.3 Quản lý Giỏ hàng (Cart Service)
*   Thêm, sửa số lượng, xóa sản phẩm khỏi giỏ hàng.
*   Lưu trữ giỏ hàng tạm thời (cần tốc độ cao, độ trễ thấp).
*   Tính tổng tiền dự kiến, hỗ trợ tích hợp với dịch vụ khuyến mãi sau này.

### 2.4 Quản lý Đơn hàng (Order Service)
*   Chuyển đổi giỏ hàng thành đơn đặt hàng.
*   Trạng thái đơn hàng: Chờ thanh toán, Đã thanh toán, Đang xử lý, Đang giao, Đã giao, Đã hủy.
*   Quản lý vòng đời đơn hàng, điều phối luồng xử lý với các service khác (Payment, Shipping).

### 2.5 Thanh toán (Payment Service)
*   Hỗ trợ đa phương thức: COD (Thanh toán khi nhận hàng), Thẻ tín dụng/ghi nợ, Ví điện tử (VNPay, MoMo, v.v.).
*   Tích hợp với Payment Gateway bên thứ 3.
*   Xử lý các nghiệp vụ hoàn tiền (Refund) khi xảy ra lỗi hoặc hủy đơn.

### 2.6 Giao hàng (Shipping Service)
*   Tích hợp các đơn vị vận chuyển (GHTK, GHN, Viettel Post...).
*   Tính toán phí giao hàng dựa trên khối lượng và khoảng cách.
*   Theo dõi hành trình đơn hàng (Tracking) và cập nhật trạng thái ngược về Order Service.

### 2.7 Tìm kiếm và Gợi ý (Search & Recommendation Service)
*   **Tìm kiếm:** Tìm kiếm full-text theo tên, mô tả, danh mục sản phẩm. Hỗ trợ lọc theo giá, thuộc tính và sắp xếp (bán chạy, mới nhất).
*   **Gợi ý:** Gợi ý sản phẩm tương tự, sản phẩm thường được mua cùng nhau.

### 2.8 Quản lý Tồn kho (Inventory Service)
*   Quản lý số lượng tồn kho của từng sản phẩm theo thời gian thực.
*   Xử lý concurrency, khóa tồn kho (reserve stock) khi người dùng đặt hàng để tránh over-selling.
*   Cập nhật lại tồn kho khi có đơn hàng bị hủy hoặc hoàn trả.

### 2.9 Khuyến mãi (Promotion Service)
*   Quản lý các chương trình khuyến mãi, Flash Sale.
*   Quản lý mã giảm giá (Voucher/Coupon), điều kiện áp dụng và giới hạn sử dụng.
*   Tính toán số tiền giảm giá và tích hợp vào Cart/Order.

## 3. Yêu cầu phi chức năng (Non-functional Requirements)
*   **Scalability (Khả năng mở rộng):** Thiết kế kiến trúc cho phép scale từng service độc lập. Ví dụ: mùa Sale có thể scale Order, Cart, Search mạnh hơn.
*   **High Availability (Tính sẵn sàng cao):** Tránh Single Point of Failure (SPOF), hệ thống luôn hoạt động ổn định.
*   **Security (Bảo mật):** Xác thực bằng JWT qua API Gateway, bảo mật dữ liệu nhạy cảm của người dùng.
*   **Maintainability (Dễ bảo trì):** Phân tách ranh giới rõ ràng giữa các service (Database per service), quản lý log tập trung, dễ dàng CI/CD.

---

## 4. Quyết định Kỹ thuật và Kiến trúc (Technical & Architectural Decisions)

1.  **Quản lý Tồn kho (Inventory):** Tách riêng thành `Inventory Service` để xử lý concurrency tốt, tránh over-selling.
2.  **Khuyến mãi/Voucher (Promotion):** Có hỗ trợ, thiết kế riêng thành `Promotion Service`.
3.  **Database Strategy:** Sử dụng **PostgreSQL** cho toàn bộ hệ thống. Đối với `Product Service` (đa ngành hàng), sẽ sử dụng kiểu dữ liệu `JSONB` của PostgreSQL để lưu trữ các thuộc tính động.
4.  **Message Broker:** Sử dụng **RabbitMQ** (hoặc Kafka) để giao tiếp bất đồng bộ giữa các service (mặc định đối với Django/Celery thường kết hợp tốt với RabbitMQ hoặc Redis).
5.  **Tech Stack:** Các microservices sẽ được phát triển bằng framework **Django** (Python).
