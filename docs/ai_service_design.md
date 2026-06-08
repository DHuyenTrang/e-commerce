# Thiết kế chi tiết AI Service

## 1. Tổng quan service

AI Service thuộc AI Service Context, cung cấp chatbot RAG, hệ thống gợi ý sản phẩm và đồng bộ tri thức sản phẩm từ Product Service sang Vector Database. Service này không thay thế Product Service; mọi thông tin nhạy cảm về giá, tồn kho hoặc trạng thái sản phẩm cần được xác minh lại với Product Service nếu cần độ chính xác thời gian thực.

Thiết kế nội bộ dùng MVC đơn giản với `AssistantController`, `RecommendationController`, `KnowledgeBaseController` và các model `ChatSession`, `ChatMessage`, `RecommendationProfile`, `KnowledgeDocument`.

## 2. Controller và phương thức

| Controller | Phương thức | Mô tả |
| --- | --- | --- |
| AssistantController | `send_query()` | Chat với AI RAG để tư vấn sản phẩm. |
| AssistantController | `get_chat_history()` | Xem lại các cuộc hội thoại tư vấn trước đó. |
| RecommendationController | `get_personalized_suggestions()` | Lấy danh sách gợi ý sản phẩm cho trang chủ. |
| RecommendationController | `get_similar_products()` | Gợi ý sản phẩm tương đương trên trang chi tiết. |
| KnowledgeBaseController | `index_product_info()` | Đồng bộ dữ liệu Catalog sang Vector Database. |

## 3. Kiến trúc nội bộ theo MVC đơn giản

```mermaid
graph TD
    Client[Client] --> Gateway[API Gateway]
    Gateway --> AssistantController[AssistantController]
    Gateway --> RecommendationController[RecommendationController]
    Gateway --> KnowledgeBaseController[KnowledgeBaseController]

    AssistantController --> ChatSessionModel[ChatSession Model]
    AssistantController --> ChatMessageModel[ChatMessage Model]
    AssistantController -. "RAG query" .-> VectorDB[(Vector Database)]
    AssistantController -. "LLM response" .-> LLM[LLM Provider]

    RecommendationController --> RecommendationModel[RecommendationProfile Model]
    RecommendationController -. "Đọc catalog" .-> ProductService[Product Service]

    KnowledgeBaseController --> KnowledgeModel[KnowledgeDocument Model]
    KnowledgeBaseController -. "Lấy catalog" .-> ProductService
    KnowledgeBaseController -. "Ghi vector" .-> VectorDB

    ChatSessionModel --> AIDB[(AI Database)]
    ChatMessageModel --> AIDB
    RecommendationModel --> AIDB
    KnowledgeModel --> AIDB
```

## 4. Use case

```mermaid
flowchart LR
    Customer((Customer))
    Staff((Staff/Admin))
    Product((Product Service))
    VectorDB((Vector Database))

    UC_Query[Chat tư vấn sản phẩm]
    UC_History[Xem lịch sử chat]
    UC_Personal[Gợi ý cá nhân hóa]
    UC_Similar[Gợi ý sản phẩm tương tự]
    UC_Index[Đồng bộ catalog sang vector]

    Customer --> UC_Query
    Customer --> UC_History
    Customer --> UC_Personal
    Customer --> UC_Similar
    Staff --> UC_Index
    UC_Index --> Product
    UC_Index --> VectorDB
```

## 5. Sơ đồ lớp thiết kế

```mermaid
classDiagram
    class AssistantController {
        +send_query(request) Response
        +get_chat_history(request) Response
    }

    class RecommendationController {
        +get_personalized_suggestions(request) Response
        +get_similar_products(request, product_id) Response
    }

    class KnowledgeBaseController {
        +index_product_info(request) Response
    }

    class ChatSession {
        +UUID id
        +UUID user_id
        +datetime created_at
        +datetime updated_at
    }

    class ChatMessage {
        +UUID id
        +UUID session_id
        +MessageRole role
        +string content
        +json sources
        +datetime created_at
    }

    class RecommendationProfile {
        +UUID id
        +UUID user_id
        +json preferences
        +datetime updated_at
    }

    class KnowledgeDocument {
        +UUID id
        +UUID product_id
        +string title
        +string content_hash
        +IndexStatus status
        +datetime indexed_at
    }

    AssistantController --> ChatSession
    AssistantController --> ChatMessage
    RecommendationController --> RecommendationProfile
    KnowledgeBaseController --> KnowledgeDocument
    ChatSession "1" --> "0..*" ChatMessage
```

## 6. Quy tắc nghiệp vụ

- Chatbot chỉ trả lời dựa trên tri thức được index và nguồn đáng tin cậy.
- Câu trả lời nên kèm nguồn sản phẩm nếu có.
- Dữ liệu giá và tồn kho cần xác minh lại với Product Service nếu hiển thị cho khách hàng.
- Lịch sử chat chỉ thuộc về user hiện tại.
- `index_product_info()` có thể chạy theo product cụ thể hoặc toàn bộ catalog.
- KnowledgeDocument cần lưu `content_hash` để tránh index lại dữ liệu không đổi.

## 7. Thiết kế API

Base path:

```text
/api/v1/ai
```

| Controller | Method | Endpoint | Auth | Mô tả |
| --- | --- | --- | --- | --- |
| AssistantController | `send_query()` | `POST /api/v1/ai/assistant/query` | Có | Chat với AI RAG. |
| AssistantController | `get_chat_history()` | `GET /api/v1/ai/assistant/history` | Có | Lịch sử hội thoại. |
| RecommendationController | `get_personalized_suggestions()` | `GET /api/v1/ai/recommendations/personalized` | Có | Gợi ý cá nhân hóa. |
| RecommendationController | `get_similar_products()` | `GET /api/v1/ai/recommendations/products/{product_id}/similar` | Không | Gợi ý sản phẩm tương tự. |
| KnowledgeBaseController | `index_product_info()` | `POST /api/v1/ai/knowledge/index-products` | Có | Đồng bộ catalog sang Vector Database. |

## 8. Sequence diagram

### 8.1 `send_query()`

```mermaid
sequenceDiagram
    participant Customer
    participant Gateway as API Gateway
    participant Controller as AssistantController
    participant ChatModel as ChatMessage Model
    participant VectorDB as Vector Database
    participant LLM as LLM Provider
    participant DB as AI DB

    Customer->>Gateway: POST /api/v1/ai/assistant/query
    Gateway->>Controller: Chuyển tiếp query/session
    Controller->>ChatModel: Lưu user message
    ChatModel->>DB: Insert ChatMessage
    Controller->>VectorDB: Tìm ngữ cảnh liên quan
    VectorDB-->>Controller: Relevant documents
    Controller->>LLM: Tạo câu trả lời từ context
    LLM-->>Controller: AI answer
    Controller->>ChatModel: Lưu assistant message
    ChatModel->>DB: Insert ChatMessage
    Controller-->>Gateway: 200 OK
    Gateway-->>Customer: Câu trả lời AI
```

### 8.2 `get_chat_history()`

```mermaid
sequenceDiagram
    participant Customer
    participant Gateway as API Gateway
    participant Controller as AssistantController
    participant ChatModel as ChatMessage Model
    participant DB as AI DB

    Customer->>Gateway: GET /api/v1/ai/assistant/history
    Gateway->>Controller: Chuyển tiếp user_id
    Controller->>ChatModel: Lấy lịch sử chat theo user
    ChatModel->>DB: Query ChatSession + ChatMessage
    DB-->>ChatModel: History
    Controller-->>Gateway: 200 OK
    Gateway-->>Customer: Chat history
```

### 8.3 `get_personalized_suggestions()`

```mermaid
sequenceDiagram
    participant Customer
    participant Gateway as API Gateway
    participant Controller as RecommendationController
    participant ProfileModel as RecommendationProfile Model
    participant Product as Product Service
    participant DB as AI DB

    Customer->>Gateway: GET /api/v1/ai/recommendations/personalized
    Gateway->>Controller: Chuyển tiếp user_id
    Controller->>ProfileModel: Lấy preference của user
    ProfileModel->>DB: Query RecommendationProfile
    DB-->>ProfileModel: Preferences
    Controller->>Product: Lấy sản phẩm phù hợp
    Product-->>Controller: Product list
    Controller-->>Gateway: 200 OK
    Gateway-->>Customer: Suggestions
```

### 8.4 `get_similar_products()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as RecommendationController
    participant VectorDB as Vector Database
    participant Product as Product Service

    Client->>Gateway: GET /api/v1/ai/recommendations/products/{id}/similar
    Gateway->>Controller: Chuyển tiếp product_id
    Controller->>VectorDB: Tìm vector sản phẩm tương tự
    VectorDB-->>Controller: Similar product_ids
    Controller->>Product: Lấy thông tin sản phẩm
    Product-->>Controller: Product list
    Controller-->>Gateway: 200 OK
    Gateway-->>Client: Similar products
```

### 8.5 `index_product_info()`

```mermaid
sequenceDiagram
    participant Staff
    participant Gateway as API Gateway
    participant Controller as KnowledgeBaseController
    participant Product as Product Service
    participant KnowledgeModel as KnowledgeDocument Model
    participant VectorDB as Vector Database
    participant DB as AI DB

    Staff->>Gateway: POST /api/v1/ai/knowledge/index-products
    Gateway->>Gateway: Xác thực quyền ai:index
    Gateway->>Controller: Chuyển tiếp product_ids/scope
    Controller->>Product: Lấy dữ liệu catalog
    Product-->>Controller: Product documents
    loop từng product
        Controller->>KnowledgeModel: Lưu/cập nhật KnowledgeDocument
        KnowledgeModel->>DB: Upsert KnowledgeDocument
        Controller->>VectorDB: Upsert embedding
    end
    Controller-->>Gateway: 202 Accepted
    Gateway-->>Staff: Index job accepted
```

## 9. Kiểm thử đề xuất

- Gửi câu hỏi RAG và nhận câu trả lời có nguồn.
- Lấy lịch sử chat đúng user.
- Gợi ý cá nhân hóa.
- Gợi ý sản phẩm tương tự.
- Index một sản phẩm.
- Index toàn bộ catalog.
- Không index lại nếu `content_hash` không đổi.
