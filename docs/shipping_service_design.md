# Thiết kế chi tiết Shipping Service

## 1. Tổng quan service

Shipping Service thuộc Shipping Context, chịu trách nhiệm tính phí vận chuyển, tạo vận đơn, theo dõi hành trình giao hàng và quản lý danh sách đối tác vận chuyển. Service này phối hợp với Order Service để cập nhật trạng thái giao hàng nhưng không sở hữu vòng đời đơn hàng tổng thể.

Thiết kế nội bộ dùng MVC đơn giản với `ShipmentController`, `AdminShippingController` và các model `Shipment`, `Carrier`, `TrackingEvent`, `ShippingRate`.

## 2. Phạm vi trách nhiệm

- Tra cứu lộ trình kiện hàng theo mã vận đơn.
- Tính phí vận chuyển dựa trên địa chỉ và khối lượng.
- Đẩy thông tin đơn hàng sang đơn vị vận chuyển.
- Cập nhật trạng thái giao hàng nội bộ.
- Quản lý danh sách đối tác giao hàng.

## 3. Kiến trúc nội bộ theo MVC đơn giản

```mermaid
graph TD
    Client[Client/Order Service] --> Gateway[API Gateway]
    CarrierWebhook[Carrier Webhook] --> Gateway
    Gateway --> ShipmentController[ShipmentController]
    Gateway --> AdminShippingController[AdminShippingController]

    ShipmentController --> ShipmentModel[Shipment Model]
    ShipmentController --> RateModel[ShippingRate Model]
    ShipmentController --> TrackingModel[TrackingEvent Model]
    AdminShippingController --> ShipmentModel
    AdminShippingController --> CarrierModel[Carrier Model]
    AdminShippingController --> TrackingModel
    AdminShippingController -. "Tạo vận đơn" .-> CarrierAPI[Carrier API]

    ShipmentModel --> ShippingDB[(Shipping Database)]
    CarrierModel --> ShippingDB
    RateModel --> ShippingDB
    TrackingModel --> ShippingDB
```

## 4. Controller và phương thức

| Controller | Phương thức | Mô tả |
| --- | --- | --- |
| ShipmentController | `track_by_number()` | Tra cứu lộ trình của kiện hàng theo mã vận đơn. |
| ShipmentController | `get_shipping_fee()` | Tính phí vận chuyển dựa trên địa chỉ và khối lượng. |
| AdminShippingController | `create_shipment_order()` | Đẩy thông tin đơn hàng sang đơn vị vận chuyển. |
| AdminShippingController | `update_tracking_status()` | Cập nhật trạng thái giao hàng nội bộ. |
| AdminShippingController | `manage_carriers()` | Quản lý danh sách các đối tác giao hàng. |

## 5. Use case

```mermaid
flowchart LR
    Customer((Customer))
    OrderService((Order Service))
    Staff((Staff/Admin))
    Carrier((Carrier API))

    UC_Track[Tra cứu vận đơn]
    UC_Fee[Tính phí vận chuyển]
    UC_Create[Tạo vận đơn]
    UC_Update[Cập nhật trạng thái giao hàng]
    UC_Carrier[Quản lý đối tác vận chuyển]

    Customer --> UC_Track
    OrderService --> UC_Fee
    OrderService --> UC_Create
    Staff --> UC_Update
    Staff --> UC_Carrier
    UC_Create --> Carrier
```

## 6. Sơ đồ lớp thiết kế

```mermaid
classDiagram
    class ShipmentController {
        +track_by_number(request, tracking_number) Response
        +get_shipping_fee(request) Response
    }

    class AdminShippingController {
        +create_shipment_order(request) Response
        +update_tracking_status(request, shipment_id) Response
        +manage_carriers(request) Response
    }

    class Shipment {
        +UUID id
        +UUID order_id
        +UUID carrier_id
        +string tracking_number
        +ShipmentStatus status
        +decimal shipping_fee
        +json receiver_address_snapshot
        +datetime created_at
        +datetime updated_at
        +change_status(status) void
    }

    class Carrier {
        +UUID id
        +string code
        +string name
        +bool is_active
        +json config
    }

    class ShippingRate {
        +UUID id
        +UUID carrier_id
        +string province
        +decimal base_fee
        +decimal fee_per_kg
    }

    class TrackingEvent {
        +UUID id
        +UUID shipment_id
        +ShipmentStatus status
        +string location
        +string description
        +datetime occurred_at
    }

    ShipmentController --> Shipment
    ShipmentController --> ShippingRate
    ShipmentController --> TrackingEvent
    AdminShippingController --> Shipment
    AdminShippingController --> Carrier
    AdminShippingController --> TrackingEvent
    Carrier "1" --> "0..*" Shipment
    Carrier "1" --> "0..*" ShippingRate
    Shipment "1" --> "0..*" TrackingEvent
```

## 7. Quy tắc nghiệp vụ

- Chỉ carrier `is_active = true` mới được dùng để tính phí hoặc tạo vận đơn.
- Khối lượng phải lớn hơn 0.
- Mỗi shipment phải gắn với một `order_id`.
- `tracking_number` phải duy nhất.
- Trạng thái giao hàng phải chuyển theo luồng hợp lệ.
- Callback từ carrier cần được xác thực nếu carrier hỗ trợ chữ ký.

## 8. Thiết kế API

Base path:

```text
/api/v1/shipping
```

| Controller | Method | Endpoint | Auth | Mô tả |
| --- | --- | --- | --- | --- |
| ShipmentController | `track_by_number()` | `GET /api/v1/shipping/track/{tracking_number}` | Không | Tra cứu vận đơn. |
| ShipmentController | `get_shipping_fee()` | `POST /api/v1/shipping/fees` | Có | Tính phí vận chuyển. |
| AdminShippingController | `create_shipment_order()` | `POST /api/v1/shipping/admin/shipments` | Có | Tạo vận đơn với carrier. |
| AdminShippingController | `update_tracking_status()` | `PATCH /api/v1/shipping/admin/shipments/{shipment_id}/tracking` | Có | Cập nhật tracking nội bộ. |
| AdminShippingController | `manage_carriers()` | `POST/PATCH /api/v1/shipping/admin/carriers` | Có | Quản lý đối tác vận chuyển. |

### 8.1 `get_shipping_fee()`

```json
{
  "province": "TP. Hồ Chí Minh",
  "district": "Quận 1",
  "weight_kg": 1.5,
  "carrier_code": "GHN"
}
```

Response:

```json
{
  "carrier_code": "GHN",
  "shipping_fee": 32000,
  "estimated_days": 3
}
```

## 9. Sequence diagram

### 9.1 `track_by_number()`

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Controller as ShipmentController
    participant ShipmentModel as Shipment Model
    participant TrackingModel as TrackingEvent Model
    participant DB as Shipping DB

    Client->>Gateway: GET /api/v1/shipping/track/{tracking_number}
    Gateway->>Controller: Chuyển tiếp tracking_number
    Controller->>ShipmentModel: Tìm Shipment
    ShipmentModel->>DB: Query Shipment
    DB-->>ShipmentModel: Shipment
    Controller->>TrackingModel: Lấy tracking events
    TrackingModel->>DB: Query TrackingEvent
    DB-->>TrackingModel: Event list
    Controller-->>Gateway: 200 OK
    Gateway-->>Client: Lộ trình vận đơn
```

### 9.2 `get_shipping_fee()`

```mermaid
sequenceDiagram
    participant Order as Order Service
    participant Gateway as API Gateway
    participant Controller as ShipmentController
    participant CarrierModel as Carrier Model
    participant RateModel as ShippingRate Model
    participant DB as Shipping DB

    Order->>Gateway: POST /api/v1/shipping/fees
    Gateway->>Controller: Chuyển tiếp địa chỉ/khối lượng
    Controller->>Controller: Validate weight/address
    Controller->>CarrierModel: Kiểm tra carrier active
    CarrierModel->>DB: Query Carrier
    DB-->>CarrierModel: Carrier
    Controller->>RateModel: Tính phí
    RateModel->>DB: Query ShippingRate
    DB-->>RateModel: Rate
    Controller-->>Gateway: 200 OK
    Gateway-->>Order: shipping_fee
```

### 9.3 `create_shipment_order()`

```mermaid
sequenceDiagram
    participant Order as Order Service
    participant Gateway as API Gateway
    participant Controller as AdminShippingController
    participant CarrierModel as Carrier Model
    participant ShipmentModel as Shipment Model
    participant CarrierAPI as Carrier API
    participant DB as Shipping DB

    Order->>Gateway: POST /api/v1/shipping/admin/shipments
    Gateway->>Controller: Chuyển tiếp order/address/items
    Controller->>CarrierModel: Kiểm tra carrier
    CarrierModel->>DB: Query Carrier
    DB-->>CarrierModel: Carrier
    Controller->>CarrierAPI: Tạo vận đơn
    CarrierAPI-->>Controller: tracking_number
    Controller->>ShipmentModel: Lưu Shipment
    ShipmentModel->>DB: Insert Shipment
    Controller-->>Gateway: 201 Created
    Gateway-->>Order: Shipment info
```

### 9.4 `update_tracking_status()`

```mermaid
sequenceDiagram
    participant Staff
    participant Gateway as API Gateway
    participant Controller as AdminShippingController
    participant ShipmentModel as Shipment Model
    participant TrackingModel as TrackingEvent Model
    participant DB as Shipping DB

    Staff->>Gateway: PATCH /api/v1/shipping/admin/shipments/{id}/tracking
    Gateway->>Controller: Chuyển tiếp status/location
    Controller->>ShipmentModel: Tìm Shipment
    ShipmentModel->>DB: Query Shipment
    DB-->>ShipmentModel: Shipment
    Controller->>ShipmentModel: Cập nhật status
    ShipmentModel->>DB: Update Shipment
    Controller->>TrackingModel: Ghi TrackingEvent
    TrackingModel->>DB: Insert TrackingEvent
    Controller-->>Gateway: 200 OK
    Gateway-->>Staff: Tracking updated
```

### 9.5 `manage_carriers()`

```mermaid
sequenceDiagram
    participant Staff
    participant Gateway as API Gateway
    participant Controller as AdminShippingController
    participant CarrierModel as Carrier Model
    participant DB as Shipping DB

    Staff->>Gateway: POST/PATCH /api/v1/shipping/admin/carriers
    Gateway->>Controller: Chuyển tiếp carrier data
    Controller->>Controller: Validate carrier code/name
    Controller->>CarrierModel: Tạo/cập nhật Carrier
    CarrierModel->>DB: Insert/Update Carrier
    Controller-->>Gateway: 200 OK hoặc 201 Created
    Gateway-->>Staff: Carrier saved
```

## 10. Kiểm thử đề xuất

- Tính phí vận chuyển hợp lệ.
- Chặn khối lượng không hợp lệ.
- Tạo vận đơn thành công.
- Cập nhật trạng thái tracking.
- Tra cứu vận đơn theo tracking number.
- Chặn carrier inactive khi tạo vận đơn.
