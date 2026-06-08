# Thiết kế chi tiết Cart Service

## 1. Tổng quan service

Cart Service thuộc Cart Context, chịu trách nhiệm quản lý giỏ hàng tạm thời của khách hàng trước khi đặt hàng. Service này lưu danh sách sản phẩm, SKU và số lượng người dùng muốn mua. Cart Service không quyết định giá cuối cùng và không sở hữu thông tin sản phẩm; khi cần hiển thị hoặc checkout, hệ thống phải xác minh lại dữ liệu với Product Service.

Thiết kế sử dụng MVC đơn giản: `CartController` nhận request, validate dữ liệu và gọi trực tiếp các model `Cart` và `CartItem`.

## 2. Phạm vi trách nhiệm

- Lấy danh sách sản phẩm đang có trong giỏ.
- Thêm sản phẩm mới vào giỏ hàng.
- Thay đổi số lượng mua của một mặt hàng.
- Loại bỏ sản phẩm khỏi giỏ hàng.

Ngoài phạm vi:

- Không tạo đơn hàng chính thức.
- Không xử lý thanh toán.
- Không sở hữu dữ liệu chi tiết sản phẩm, giá bán hoặc tồn kho.
- Không tính phí vận chuyển.

## 3. Kiến trúc nội bộ theo MVC đơn giản

```mermaid
graph TD
    Client[Web/Mobile Client] --> Gateway[API Gateway]
    Gateway --> CartController[CartController]

    CartController --> CartModel[Cart Model]
    CartController --> CartItemModel[CartItem Model]
    CartController -. "Lấy thông tin hiển thị" .-> ProductService[Product Service]

    CartModel --> CartDB[(Cart Database)]
    CartItemModel --> CartDB
```

| Thành phần | Trách nhiệm |
| --- | --- |
| CartController | Xử lý request xem, thêm, cập nhật và xóa item trong giỏ hàng. |
| Cart Model | Lưu giỏ hàng active của customer hoặc guest session. |
| CartItem Model | Lưu từng mặt hàng trong giỏ: product, SKU và số lượng. |
| Product Service | Cung cấp thông tin sản phẩm khi cần hiển thị hoặc xác minh. |

## 4. Controller và phương thức

| Controller | Phương thức | Mô tả |
| --- | --- | --- |
| CartController | `get_cart()` | Lấy danh sách các sản phẩm đang có trong giỏ. |
| CartController | `add_item()` | Thêm một sản phẩm mới vào giỏ hàng. |
| CartController | `update_item_quantity()` | Thay đổi số lượng mua của một mặt hàng. |
| CartController | `remove_item()` | Loại bỏ sản phẩm ra khỏi giỏ hàng. |

## 5. Use case

### 5.1 Sơ đồ use case

```mermaid
flowchart LR
    Guest((Guest))
    Customer((Customer))
    ProductService((Product Service))

    UC_GetCart[Xem giỏ hàng]
    UC_AddItem[Thêm sản phẩm vào giỏ]
    UC_UpdateQuantity[Cập nhật số lượng]
    UC_RemoveItem[Xóa sản phẩm khỏi giỏ]
    UC_VerifyProduct[Xác minh sản phẩm]

    Guest --> UC_GetCart
    Guest --> UC_AddItem
    Guest --> UC_UpdateQuantity
    Guest --> UC_RemoveItem

    Customer --> UC_GetCart
    Customer --> UC_AddItem
    Customer --> UC_UpdateQuantity
    Customer --> UC_RemoveItem

    UC_AddItem --> UC_VerifyProduct
    UC_UpdateQuantity --> UC_VerifyProduct
    ProductService --> UC_VerifyProduct
```

### 5.2 Mô tả use case

| Use case | Tác nhân | Mô tả | Ngoại lệ chính |
| --- | --- | --- | --- |
| Xem giỏ hàng | Guest, Customer | Lấy giỏ hàng active và danh sách item. | Giỏ hàng chưa tồn tại thì trả giỏ rỗng. |
| Thêm sản phẩm | Guest, Customer | Thêm product/SKU vào giỏ; nếu item đã tồn tại thì tăng số lượng. | Sản phẩm không tồn tại, ngừng bán hoặc số lượng không hợp lệ. |
| Cập nhật số lượng | Guest, Customer | Thay đổi số lượng của một item. | Item không tồn tại, số lượng nhỏ hơn 1. |
| Xóa sản phẩm | Guest, Customer | Xóa item khỏi giỏ hàng. | Item không tồn tại hoặc không thuộc giỏ hiện tại. |

## 6. Sơ đồ lớp thiết kế

```mermaid
classDiagram
    class CartController {
        +get_cart(request) Response
        +add_item(request) Response
        +update_item_quantity(request, item_id) Response
        +remove_item(request, item_id) Response
    }

    class Cart {
        +UUID id
        +UUID user_id
        +string guest_session_id
        +CartStatus status
        +datetime created_at
        +datetime updated_at
        +is_active() bool
    }

    class CartItem {
        +UUID id
        +UUID cart_id
        +UUID product_id
        +string sku
        +int quantity
        +datetime added_at
        +datetime updated_at
        +update_quantity(quantity) void
    }

    CartController --> Cart
    CartController --> CartItem
    Cart "1" --> "0..*" CartItem
```

## 7. Entity đề xuất

### Cart

| Trường | Kiểu | Mô tả |
| --- | --- | --- |
| `id` | UUID | Khóa chính của giỏ hàng. |
| `user_id` | UUID | Khách hàng sở hữu giỏ, null với guest. |
| `guest_session_id` | string | Định danh giỏ hàng guest. |
| `status` | enum | `ACTIVE`, `CHECKED_OUT`, `ABANDONED`. |
| `created_at` | datetime | Thời điểm tạo. |
| `updated_at` | datetime | Thời điểm cập nhật. |

### CartItem

| Trường | Kiểu | Mô tả |
| --- | --- | --- |
| `id` | UUID | Khóa chính của item. |
| `cart_id` | UUID | Giỏ hàng chứa item. |
| `product_id` | UUID | Sản phẩm được thêm vào giỏ. |
| `sku` | string | SKU hoặc biến thể sản phẩm. |
| `quantity` | integer | Số lượng muốn mua. |
| `added_at` | datetime | Thời điểm thêm vào giỏ. |
| `updated_at` | datetime | Thời điểm cập nhật. |

## 8. Quy tắc nghiệp vụ

- Mỗi customer chỉ có một giỏ hàng `ACTIVE` tại một thời điểm.
- Guest có thể có giỏ hàng theo `guest_session_id`.
- `quantity` phải lớn hơn 0.
- Nếu thêm item đã tồn tại trong giỏ, hệ thống cộng dồn số lượng.
- Cart Service chỉ lưu `product_id`, `sku`, `quantity`; giá và tồn kho phải xác minh lại với Product Service khi hiển thị hoặc checkout.
- Khi Order Service tạo đơn thành công, giỏ hàng có thể chuyển sang `CHECKED_OUT`.

## 9. Thiết kế API

Base path:

```text
/api/v1/cart
```

| Controller | Method | Endpoint | Auth | Mô tả |
| --- | --- | --- | --- | --- |
| CartController | `get_cart()` | `GET /api/v1/cart` | Tùy chọn | Lấy giỏ hàng hiện tại. |
| CartController | `add_item()` | `POST /api/v1/cart/items` | Tùy chọn | Thêm item vào giỏ. |
| CartController | `update_item_quantity()` | `PATCH /api/v1/cart/items/{item_id}` | Tùy chọn | Cập nhật số lượng item. |
| CartController | `remove_item()` | `DELETE /api/v1/cart/items/{item_id}` | Tùy chọn | Xóa item khỏi giỏ. |

### 9.1 `get_cart()`

```http
GET /api/v1/cart
Authorization: Bearer <access_token>
```

Response `200 OK`:

```json
{
  "id": "cart-001",
  "status": "ACTIVE",
  "items": [
    {
      "id": "item-001",
      "product_id": "product-001",
      "sku": "TSHIRT-BASIC-001",
      "quantity": 2
    }
  ]
}
```

### 9.2 `add_item()`

```http
POST /api/v1/cart/items
```

Request:

```json
{
  "product_id": "product-001",
  "sku": "TSHIRT-BASIC-001",
  "quantity": 1
}
```

Response `201 Created`.

### 9.3 `update_item_quantity()`

```http
PATCH /api/v1/cart/items/{item_id}
```

Request:

```json
{
  "quantity": 3
}
```

Response `200 OK`.

### 9.4 `remove_item()`

```http
DELETE /api/v1/cart/items/{item_id}
```

Response `204 No Content`.

### 9.5 Lỗi thường gặp

| HTTP status | Code | Mô tả |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | Dữ liệu sai định dạng. |
| 404 | `CART_NOT_FOUND` | Không tìm thấy giỏ hàng. |
| 404 | `CART_ITEM_NOT_FOUND` | Không tìm thấy item. |
| 409 | `PRODUCT_NOT_AVAILABLE` | Sản phẩm không còn khả dụng. |
| 409 | `INVALID_QUANTITY` | Số lượng không hợp lệ. |

## 10. Sequence diagram

### 10.1 `get_cart()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as CartController
    participant CartModel as Cart Model
    participant ItemModel as CartItem Model
    participant DB as Cart DB

    Client->>Gateway: GET /api/v1/cart
    Gateway->>Controller: Chuyển tiếp user/session
    Controller->>CartModel: Tìm giỏ hàng active
    CartModel->>DB: Query Cart
    DB-->>CartModel: Cart
    Controller->>ItemModel: Lấy item theo cart_id
    ItemModel->>DB: Query CartItem
    DB-->>ItemModel: Item list
    Controller-->>Gateway: 200 OK
    Gateway-->>Client: Giỏ hàng
```

### 10.2 `add_item()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as CartController
    participant Product as Product Service
    participant CartModel as Cart Model
    participant ItemModel as CartItem Model
    participant DB as Cart DB

    Client->>Gateway: POST /api/v1/cart/items
    Gateway->>Controller: Chuyển tiếp request
    Controller->>Controller: Validate product_id/sku/quantity
    Controller->>Product: Kiểm tra sản phẩm khả dụng
    Product-->>Controller: Sản phẩm hợp lệ
    Controller->>CartModel: Lấy hoặc tạo Cart active
    CartModel->>DB: Query/Insert Cart
    Controller->>ItemModel: Tìm item hiện có
    ItemModel->>DB: Query CartItem
    alt item đã tồn tại
        Controller->>ItemModel: Cộng dồn quantity
        ItemModel->>DB: Update CartItem
    else item chưa tồn tại
        Controller->>ItemModel: Tạo CartItem
        ItemModel->>DB: Insert CartItem
    end
    Controller-->>Gateway: 201 Created
    Gateway-->>Client: Item trong giỏ
```

### 10.3 `update_item_quantity()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as CartController
    participant Product as Product Service
    participant ItemModel as CartItem Model
    participant DB as Cart DB

    Client->>Gateway: PATCH /api/v1/cart/items/{item_id}
    Gateway->>Controller: Chuyển tiếp item_id và quantity
    Controller->>Controller: Validate quantity > 0
    Controller->>ItemModel: Tìm item thuộc giỏ hiện tại
    ItemModel->>DB: Query CartItem
    DB-->>ItemModel: CartItem
    Controller->>Product: Kiểm tra sản phẩm/SKU khả dụng
    Product-->>Controller: Hợp lệ
    Controller->>ItemModel: Cập nhật quantity
    ItemModel->>DB: Update CartItem
    Controller-->>Gateway: 200 OK
    Gateway-->>Client: Item đã cập nhật
```

### 10.4 `remove_item()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as CartController
    participant ItemModel as CartItem Model
    participant DB as Cart DB

    Client->>Gateway: DELETE /api/v1/cart/items/{item_id}
    Gateway->>Controller: Chuyển tiếp item_id
    Controller->>ItemModel: Tìm item thuộc giỏ hiện tại
    ItemModel->>DB: Query CartItem
    DB-->>ItemModel: CartItem
    Controller->>ItemModel: Xóa CartItem
    ItemModel->>DB: Delete CartItem
    Controller-->>Gateway: 204 No Content
    Gateway-->>Client: Xóa thành công
```

## 11. Tích hợp service khác

| Service | Mục đích |
| --- | --- |
| Product Service | Xác minh sản phẩm, SKU, trạng thái bán và thông tin hiển thị. |
| Order Service | Lấy giỏ hàng để tạo đơn và chuyển giỏ sang `CHECKED_OUT`. |
| User Service | Xác định `user_id` khi khách hàng đăng nhập. |

## 12. Kiểm thử đề xuất

- Lấy giỏ rỗng.
- Thêm item mới.
- Thêm item đã tồn tại và cộng dồn số lượng.
- Cập nhật số lượng hợp lệ.
- Chặn số lượng nhỏ hơn 1.
- Xóa item khỏi giỏ.
- Chặn sửa/xóa item không thuộc giỏ hiện tại.
