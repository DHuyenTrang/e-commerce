# Thiết kế chi tiết Comment Service

## 1. Tổng quan service

Comment Service thuộc Comment Context, chịu trách nhiệm quản lý đánh giá sản phẩm, bình luận phản hồi và kiểm duyệt nội dung. Service này liên kết khách hàng và sản phẩm thông qua `user_id` và `product_id`, nhưng không sở hữu dữ liệu chi tiết của User Service hoặc Product Service.

Thiết kế nội bộ dùng MVC đơn giản với `ReviewController`, `CommentController` và các model `Review`, `CommentReply`, `CommentModeration`.

## 2. Controller và phương thức

| Controller | Phương thức | Mô tả |
| --- | --- | --- |
| ReviewController | `submit_review()` | Đăng tải nhận xét và số sao cho sản phẩm. |
| ReviewController | `get_product_reviews()` | Lấy toàn bộ đánh giá của một sản phẩm cụ thể. |
| CommentController | `post_reply()` | Phản hồi lại đánh giá của khách hàng. |
| CommentController | `moderate_comment()` | Ẩn/hiện các bình luận vi phạm chính sách. |

## 3. Kiến trúc nội bộ theo MVC đơn giản

```mermaid
graph TD
    Client[Client/Admin Portal] --> Gateway[API Gateway]
    Gateway --> ReviewController[ReviewController]
    Gateway --> CommentController[CommentController]

    ReviewController --> ReviewModel[Review Model]
    CommentController --> ReplyModel[CommentReply Model]
    CommentController --> ModerationModel[CommentModeration Model]

    ReviewController -. "Xác minh sản phẩm" .-> ProductService[Product Service]
    ReviewController -. "Xác minh user/order nếu cần" .-> UserOrder[User/Order Service]

    ReviewModel --> CommentDB[(Comment Database)]
    ReplyModel --> CommentDB
    ModerationModel --> CommentDB
```

## 4. Use case

```mermaid
flowchart LR
    Customer((Customer))
    Staff((Staff/Admin))
    Product((Product Service))

    UC_Submit[Đăng đánh giá]
    UC_Get[Lấy đánh giá sản phẩm]
    UC_Reply[Phản hồi đánh giá]
    UC_Moderate[Ẩn/hiện bình luận]

    Customer --> UC_Submit
    Customer --> UC_Get
    Staff --> UC_Reply
    Staff --> UC_Moderate
    UC_Submit --> Product
    UC_Get --> Product
```

## 5. Sơ đồ lớp thiết kế

```mermaid
classDiagram
    class ReviewController {
        +submit_review(request) Response
        +get_product_reviews(request, product_id) Response
    }

    class CommentController {
        +post_reply(request, review_id) Response
        +moderate_comment(request, comment_id) Response
    }

    class Review {
        +UUID id
        +UUID product_id
        +UUID user_id
        +UUID order_id
        +int rating
        +string content
        +ReviewStatus status
        +datetime created_at
        +datetime updated_at
        +hide() void
        +show() void
    }

    class CommentReply {
        +UUID id
        +UUID review_id
        +UUID staff_id
        +string content
        +CommentStatus status
        +datetime created_at
    }

    class CommentModeration {
        +UUID id
        +string target_type
        +UUID target_id
        +ModerationAction action
        +UUID moderated_by
        +string reason
        +datetime created_at
    }

    ReviewController --> Review
    CommentController --> CommentReply
    CommentController --> CommentModeration
    Review "1" --> "0..*" CommentReply
```

## 6. Quy tắc nghiệp vụ

- `rating` phải nằm trong khoảng 1 đến 5.
- Review phải gắn với một `product_id` hợp lệ.
- Customer chỉ được sửa/xóa review của chính mình nếu chức năng này được bổ sung sau.
- Có thể yêu cầu `order_id` để xác minh người dùng đã mua hàng trước khi đánh giá.
- Staff/Admin có thể phản hồi review.
- Nội dung vi phạm có thể bị ẩn nhưng nên giữ lại dữ liệu để audit.

## 7. Thiết kế API

Base path:

```text
/api/v1/comments
```

| Controller | Method | Endpoint | Auth | Mô tả |
| --- | --- | --- | --- | --- |
| ReviewController | `submit_review()` | `POST /api/v1/comments/reviews` | Có | Đăng đánh giá sản phẩm. |
| ReviewController | `get_product_reviews()` | `GET /api/v1/comments/products/{product_id}/reviews` | Không | Lấy đánh giá theo sản phẩm. |
| CommentController | `post_reply()` | `POST /api/v1/comments/reviews/{review_id}/replies` | Có | Phản hồi đánh giá. |
| CommentController | `moderate_comment()` | `PATCH /api/v1/comments/moderation/{target_type}/{target_id}` | Có | Ẩn/hiện nội dung vi phạm. |

### 7.1 `submit_review()`

```json
{
  "product_id": "product-001",
  "order_id": "order-001",
  "rating": 5,
  "content": "Sản phẩm tốt, giao nhanh."
}
```

### 7.2 `post_reply()`

```json
{
  "content": "Cảm ơn bạn đã đánh giá sản phẩm."
}
```

### 7.3 `moderate_comment()`

```json
{
  "action": "HIDE",
  "reason": "Nội dung vi phạm chính sách"
}
```

## 8. Sequence diagram

### 8.1 `submit_review()`

```mermaid
sequenceDiagram
    participant Customer
    participant Gateway as API Gateway
    participant Controller as ReviewController
    participant Product as Product Service
    participant Order as Order Service
    participant ReviewModel as Review Model
    participant DB as Comment DB

    Customer->>Gateway: POST /api/v1/comments/reviews
    Gateway->>Controller: Chuyển tiếp user_id và body
    Controller->>Controller: Validate rating/content
    Controller->>Product: Kiểm tra product_id
    Product-->>Controller: Product hợp lệ
    opt cần xác minh đã mua hàng
        Controller->>Order: Kiểm tra order_id thuộc user/product
        Order-->>Controller: Hợp lệ
    end
    Controller->>ReviewModel: Tạo Review
    ReviewModel->>DB: Insert Review
    Controller-->>Gateway: 201 Created
    Gateway-->>Customer: Review đã tạo
```

### 8.2 `get_product_reviews()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as ReviewController
    participant ReviewModel as Review Model
    participant ReplyModel as CommentReply Model
    participant DB as Comment DB

    Client->>Gateway: GET /api/v1/comments/products/{product_id}/reviews
    Gateway->>Controller: Chuyển tiếp product_id
    Controller->>ReviewModel: Lấy review visible
    ReviewModel->>DB: Query Review
    DB-->>ReviewModel: Review list
    Controller->>ReplyModel: Lấy replies visible
    ReplyModel->>DB: Query CommentReply
    DB-->>ReplyModel: Reply list
    Controller-->>Gateway: 200 OK
    Gateway-->>Client: Product reviews
```

### 8.3 `post_reply()`

```mermaid
sequenceDiagram
    participant Staff
    participant Gateway as API Gateway
    participant Controller as CommentController
    participant ReviewModel as Review Model
    participant ReplyModel as CommentReply Model
    participant DB as Comment DB

    Staff->>Gateway: POST /api/v1/comments/reviews/{review_id}/replies
    Gateway->>Gateway: Xác thực quyền comment:reply
    Gateway->>Controller: Chuyển tiếp staff_id/content
    Controller->>ReviewModel: Kiểm tra review tồn tại
    ReviewModel->>DB: Query Review
    DB-->>ReviewModel: Review
    Controller->>ReplyModel: Tạo reply
    ReplyModel->>DB: Insert CommentReply
    Controller-->>Gateway: 201 Created
    Gateway-->>Staff: Reply created
```

### 8.4 `moderate_comment()`

```mermaid
sequenceDiagram
    participant Staff
    participant Gateway as API Gateway
    participant Controller as CommentController
    participant ReviewModel as Review Model
    participant ReplyModel as CommentReply Model
    participant ModerationModel as CommentModeration Model
    participant DB as Comment DB

    Staff->>Gateway: PATCH /api/v1/comments/moderation/{target_type}/{target_id}
    Gateway->>Gateway: Xác thực quyền comment:moderate
    Gateway->>Controller: Chuyển tiếp action/reason
    alt target_type = review
        Controller->>ReviewModel: Ẩn/hiện Review
        ReviewModel->>DB: Update Review status
    else target_type = reply
        Controller->>ReplyModel: Ẩn/hiện Reply
        ReplyModel->>DB: Update CommentReply status
    end
    Controller->>ModerationModel: Ghi log kiểm duyệt
    ModerationModel->>DB: Insert CommentModeration
    Controller-->>Gateway: 200 OK
    Gateway-->>Staff: Moderation result
```

## 9. Kiểm thử đề xuất

- Đăng review hợp lệ.
- Chặn rating ngoài khoảng 1-5.
- Lấy review theo sản phẩm.
- Staff phản hồi review.
- Ẩn/hiện review hoặc reply.
- Chặn customer đánh giá sản phẩm không tồn tại.
