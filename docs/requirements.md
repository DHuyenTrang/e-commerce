# Phân tích nghiệp vụ E-Commerce Microservices

## 1. Tổng quan nghiệp vụ

Hệ thống E-Commerce hỗ trợ khách hàng tìm kiếm sản phẩm, quản lý giỏ hàng, đặt hàng, thanh toán, theo dõi vận chuyển, đánh giá sản phẩm và nhận hỗ trợ từ chatbot AI. Phía quản trị hỗ trợ nhân sự vận hành hệ thống, quản lý catalog, xử lý đơn hàng, theo dõi giao dịch và quản lý quyền truy cập.

Hệ thống được chia thành 09 bounded context tương ứng với 09 microservices:

- User Service trong Customer Context.
- Staff Service trong Staff Context.
- Product Service trong Catalog Context.
- Cart Service trong Cart Context.
- Order Service trong Ordering Context.
- Payment Service trong Payment Context.
- Shipping Service trong Shipping Context.
- AI Service trong AI Service Context.
- Comment Service trong Comment Context.

## 2. Tác nhân nghiệp vụ

| Tác nhân | Mô tả |
| --- | --- |
| Guest | Người dùng chưa đăng nhập, có thể xem sản phẩm và tìm kiếm cơ bản. |
| Customer | Khách hàng đã đăng ký, có thể quản lý hồ sơ, giỏ hàng, đặt hàng, thanh toán và đánh giá sản phẩm. |
| Staff | Nhân sự vận hành, thực hiện các tác vụ được phân quyền. |
| Admin | Quản trị viên có quyền quản lý nhân sự, vai trò, quyền và cấu hình hệ thống. |
| Payment Provider | Cổng thanh toán bên thứ ba hoặc kênh thanh toán nội bộ. |
| Shipping Provider | Đơn vị vận chuyển bên thứ ba hoặc đội giao hàng nội bộ. |
| AI Assistant | Tác nhân phản hồi câu hỏi, gợi ý sản phẩm và khai thác tri thức sản phẩm. |

## 3. Phạm vi nghiệp vụ theo service

### 3.1 User Service

Mục tiêu: quản lý định danh và thông tin khách hàng.

Chức năng chính:

- Đăng ký tài khoản khách hàng.
- Đăng nhập, đăng xuất và quản lý token.
- Kích hoạt tài khoản qua email/mã xác thực.
- Quản lý hồ sơ cá nhân: họ tên, số điện thoại, email, ngày sinh, giới tính.
- Quản lý sổ địa chỉ giao hàng.
- Quản lý trạng thái tài khoản: active, inactive, locked, pending verification.
- Cung cấp thông tin định danh cho các service khác thông qua API.

Quy tắc nghiệp vụ:

- Email hoặc số điện thoại đăng nhập phải duy nhất.
- Tài khoản chưa kích hoạt bị giới hạn các hành động nhạy cảm như đặt hàng hoặc thanh toán.
- Khách hàng có thể có nhiều địa chỉ, nhưng chỉ nên có một địa chỉ mặc định.
- Dữ liệu nhạy cảm không được chia sẻ trực tiếp cho service khác nếu không cần thiết.

### 3.2 Staff Service

Mục tiêu: quản trị nhân sự và phân quyền hệ thống theo RBAC.

Chức năng chính:

- Quản lý tài khoản nhân sự nội bộ.
- Quản lý phòng ban, chức vụ và trạng thái làm việc.
- Quản lý role và permission.
- Gán role/permission cho staff.
- Xác minh quyền truy cập cho các tác vụ quản trị.
- Ghi audit log cho hành động quan trọng.

Quy tắc nghiệp vụ:

- Chỉ Admin hoặc role được ủy quyền mới được tạo và cấp quyền staff.
- Quyền nên được mô tả theo cấu trúc `resource:action`, ví dụ `product:create`, `order:update_status`.
- Các thao tác thay đổi quyền phải được ghi audit.
- Staff bị khóa tài khoản không được truy cập API quản trị.

### 3.3 Product Service

Mục tiêu: quản lý catalog sản phẩm và tồn kho.

Chức năng chính:

- Quản lý sản phẩm, SKU và biến thể sản phẩm.
- Quản lý danh mục sản phẩm theo cây phân cấp.
- Quản lý thương hiệu.
- Quản lý nhãn/tag phục vụ lọc, tìm kiếm và gợi ý.
- Quản lý giá bán, giá gốc, trạng thái hiển thị.
- Quản lý hình ảnh và mô tả sản phẩm.
- Quản lý tồn kho và khả dụng bán hàng.
- Cung cấp dữ liệu sản phẩm cho Cart, Order, Comment và AI Service.

Quy tắc nghiệp vụ:

- Sản phẩm chỉ được hiển thị khi trạng thái là active và còn hiệu lực kinh doanh.
- SKU phải duy nhất trong Product Service.
- Tồn kho khả dụng phải được kiểm tra trước khi Order Service tạo đơn.
- Giá sản phẩm tại thời điểm đặt hàng cần được Order Service lưu snapshot vào đơn hàng.
- Product Service là source of truth cho dữ liệu catalog; AI Service và Comment Service chỉ tham chiếu bằng ID hoặc bản sao phục vụ đọc.

### 3.4 Cart Service

Mục tiêu: quản lý giỏ hàng tạm thời của khách hàng.

Chức năng chính:

- Tạo giỏ hàng cho customer hoặc guest session.
- Thêm sản phẩm vào giỏ hàng.
- Cập nhật số lượng item.
- Xóa item khỏi giỏ hàng.
- Lấy giỏ hàng hiện tại.
- Xóa giỏ hàng sau khi đặt hàng thành công.

Quy tắc nghiệp vụ:

- Mỗi customer nên có một giỏ hàng active tại một thời điểm.
- Số lượng item phải lớn hơn 0.
- Cart Service chỉ lưu dữ liệu tạm thời như `product_id`, `sku_id`, `quantity`; giá và tồn kho cần xác minh lại với Product Service khi checkout.
- Giỏ hàng guest có thể được merge vào giỏ hàng customer sau khi đăng nhập.

### 3.5 Order Service

Mục tiêu: điều phối quy trình đặt hàng và quản lý vòng đời đơn hàng.

Chức năng chính:

- Tạo đơn hàng từ giỏ hàng.
- Xác minh sản phẩm, giá và tồn kho với Product Service.
- Tính tổng tiền đơn hàng, phí vận chuyển và các khoản thanh toán.
- Điều phối Payment Service để tạo/thực hiện thanh toán.
- Điều phối Shipping Service để tính phí và tạo vận đơn.
- Quản lý trạng thái đơn hàng.
- Lưu snapshot thông tin sản phẩm, địa chỉ giao hàng và giá tại thời điểm đặt hàng.
- Cung cấp lịch sử đơn hàng cho customer và staff.

Quy tắc nghiệp vụ:

- Order Service là service orchestration trong quy trình đặt hàng.
- Đơn hàng phải có ít nhất một item hợp lệ.
- Đơn hàng cần lưu snapshot giá sản phẩm để tránh thay đổi khi catalog cập nhật.
- Trạng thái đơn hàng chỉ được chuyển theo luồng hợp lệ.
- Đơn hàng đã thanh toán cần có liên kết đến giao dịch thanh toán.
- Hủy đơn sau khi đã thanh toán cần kích hoạt quy trình refund nếu thỏa điều kiện.

### 3.6 Payment Service

Mục tiêu: xử lý thanh toán và quản lý lịch sử giao dịch.

Chức năng chính:

- Quản lý phương thức thanh toán của khách hàng nếu có.
- Tạo payment session/payment intent cho đơn hàng.
- Xử lý thanh toán COD, ví điện tử, chuyển khoản hoặc cổng thanh toán bên thứ ba.
- Nhận callback/webhook từ payment provider.
- Cập nhật trạng thái giao dịch.
- Xử lý hoàn tiền.
- Cung cấp lịch sử giao dịch cho Order Service và customer.

Quy tắc nghiệp vụ:

- Mỗi giao dịch phải gắn với một `order_id`.
- Giao dịch thanh toán cần có mã tham chiếu duy nhất để đối soát.
- API thanh toán cần hỗ trợ idempotency để tránh tính tiền nhiều lần.
- Payment Service không tự ý thay đổi trạng thái đơn hàng, mà trả kết quả cho Order Service.
- Thông tin nhạy cảm về thẻ/ngân hàng phải được tokenization hoặc xử lý qua provider đạt chuẩn bảo mật.

### 3.7 Shipping Service

Mục tiêu: tính phí giao hàng, quản lý vận đơn và theo dõi hành trình.

Chức năng chính:

- Quản lý đơn vị vận chuyển.
- Tính phí vận chuyển theo địa chỉ, khối lượng, kích thước và phương thức giao.
- Tạo vận đơn cho đơn hàng.
- Cập nhật tracking và trạng thái giao hàng.
- Nhận callback/webhook từ shipping provider.
- Cung cấp thông tin tracking cho Order Service và customer.

Quy tắc nghiệp vụ:

- Phí vận chuyển phải được tính trước khi xác nhận tổng tiền đơn hàng.
- Vận đơn phải gắn với một `order_id`.
- Trạng thái vận chuyển cần được mapping về trạng thái đơn hàng khi cần.
- Nếu tạo vận đơn thất bại, Order Service phải nhận được lỗi rõ ràng để cập nhật đơn hàng.

### 3.8 AI Service

Mục tiêu: cung cấp chatbot RAG, gợi ý sản phẩm và quản trị tri thức sản phẩm.

Chức năng chính:

- Đồng bộ dữ liệu sản phẩm từ Product Service.
- Tạo embedding và lưu vào Vector Database.
- Trả lời câu hỏi về sản phẩm bằng chatbot RAG.
- Gợi ý sản phẩm dựa trên câu hỏi, hành vi hoặc ngữ cảnh khách hàng.
- Quản lý kho tri thức, câu hỏi thường gặp và nội dung hỗ trợ.
- Ghi log hỏi đáp để đánh giá chất lượng phản hồi.

Quy tắc nghiệp vụ:

- Product Service là source of truth, AI Service chỉ giữ bản sao phục vụ truy vấn.
- Nội dung trả lời về giá, tồn kho và trạng thái sản phẩm cần được xác minh lại với Product Service nếu cần độ chính xác thời gian thực.
- Chatbot không được đưa ra thông tin thanh toán, chính sách hoặc cam kết vượt quá dữ liệu được phê duyệt.
- Dữ liệu người dùng dùng cho gợi ý cần tuân thủ nguyên tắc bảo mật và tối thiểu hóa dữ liệu.

### 3.9 Comment Service

Mục tiêu: quản lý đánh giá sản phẩm, bình luận và phản hồi của khách hàng.

Chức năng chính:

- Tạo đánh giá sản phẩm.
- Cập nhật/xóa đánh giá theo quyền.
- Quản lý điểm đánh giá, nội dung bình luận, hình ảnh đính kèm.
- Quản lý phản hồi của staff hoặc shop.
- Lọc và hiển thị đánh giá theo product.
- Xác minh liên kết User và Product qua `user_id`, `product_id`.
- Hỗ trợ cơ chế đánh giá đã mua hàng nếu liên kết với Order Service.

Quy tắc nghiệp vụ:

- Chỉ customer hợp lệ mới được tạo đánh giá.
- Mỗi customer có thể bị giới hạn số lần đánh giá cho một sản phẩm tùy theo chính sách.
- Đánh giá vi phạm có thể bị ẩn hoặc xóa mềm.
- Comment Service không sở hữu dữ liệu chi tiết của User hoặc Product, chỉ lưu ID và snapshot tối thiểu nếu cần hiển thị.

## 4. Quy trình nghiệp vụ chính

### 4.1 Đăng ký và kích hoạt tài khoản

1. Customer gửi thông tin đăng ký.
2. User Service kiểm tra trùng email/số điện thoại.
3. User Service tạo tài khoản trạng thái pending verification.
4. Hệ thống gửi mã kích hoạt.
5. Customer xác minh mã.
6. User Service chuyển tài khoản sang active.

### 4.2 Quản lý giỏ hàng

1. Customer thêm sản phẩm vào giỏ hàng.
2. Cart Service lưu `product_id`, `sku_id`, `quantity`.
3. Khi hiển thị giỏ hàng, Cart Service hoặc client lấy thông tin sản phẩm hiện tại từ Product Service.
4. Customer cập nhật/xóa item nếu cần.

### 4.3 Đặt hàng

1. Customer yêu cầu checkout.
2. Order Service lấy giỏ hàng từ Cart Service.
3. Order Service kiểm tra sản phẩm, giá và tồn kho với Product Service.
4. Order Service yêu cầu Shipping Service tính phí vận chuyển.
5. Order Service tạo đơn hàng và lưu snapshot.
6. Order Service yêu cầu Payment Service tạo giao dịch thanh toán.
7. Khi thanh toán hợp lệ, Order Service yêu cầu Shipping Service tạo vận đơn.
8. Order Service cập nhật trạng thái và trả kết quả cho customer.

### 4.4 Thanh toán

1. Customer chọn phương thức thanh toán.
2. Payment Service tạo giao dịch với trạng thái pending.
3. Payment Provider xử lý thanh toán.
4. Payment Service nhận kết quả thanh toán.
5. Order Service cập nhật đơn hàng theo kết quả thanh toán.

### 4.5 Giao hàng

1. Order Service yêu cầu Shipping Service tạo vận đơn.
2. Shipping Service gọi shipping provider.
3. Shipping Service lưu mã vận đơn và trạng thái tracking.
4. Shipping Service cập nhật hành trình khi provider gửi callback hoặc khi hệ thống polling.
5. Order Service cập nhật trạng thái đơn hàng tương ứng.

### 4.6 Đánh giá sản phẩm

1. Customer gửi đánh giá cho `product_id`.
2. Comment Service xác minh customer và product tồn tại khi cần.
3. Comment Service có thể xác minh đơn hàng đã mua nếu chính sách yêu cầu.
4. Comment Service lưu đánh giá và trạng thái hiển thị.
5. Product Service hoặc client có thể lấy thông tin tổng hợp điểm đánh giá để hiển thị.

### 4.7 Chatbot và gợi ý sản phẩm

1. AI Service đồng bộ dữ liệu sản phẩm từ Product Service.
2. AI Service xử lý embedding và lưu Vector Database.
3. Customer gửi câu hỏi qua chatbot.
4. AI Service truy vấn Vector Database để lấy ngữ cảnh liên quan.
5. AI Service tạo câu trả lời và gợi ý sản phẩm.
6. Nếu cần thông tin giá/tồn kho hiện tại, AI Service xác minh lại với Product Service.

## 5. Yêu cầu phi chức năng

### 5.1 Khả năng mở rộng

- Product, Cart, Order và AI Service cần có khả năng scale độc lập.
- API Gateway cần hỗ trợ cân bằng tải và rate limit.
- Vector Database cần được thiết kế để mở rộng theo số lượng sản phẩm và tài liệu tri thức.

### 5.2 Bảo mật

- Sử dụng JWT cho xác thực request.
- Staff Service quản lý RBAC cho API quản trị.
- Payment Service không lưu dữ liệu thẻ nhạy cảm nếu không cần thiết.
- Audit log bắt buộc cho các hành động quản trị, thanh toán và thay đổi quyền.

### 5.3 Tính sẵn sàng và chịu lỗi

- Các request liên service cần có timeout rõ ràng.
- Lỗi từ Payment/Shipping/Product cần được Order Service xử lý thành trạng thái nghiệp vụ.
- Các thao tác quan trọng cần có idempotency key.
- Hệ thống cần có logging và tracing để theo dõi luồng checkout.

### 5.4 Bảo trì và mở rộng

- Mỗi service có module, database migration và API contract riêng.
- Không chia sẻ model database giữa các service.
- Tài liệu từng service sẽ được bổ sung sau theo cùng một mẫu: mục tiêu, data model, API, business rules, error cases và test cases.

## 6. Giả định và điểm cần bổ sung sau

Tài liệu này đặt nền tảng nghiệp vụ tổng thể. Các chi tiết sau cần được cập nhật khi thiết kế từng service:

- Cấu trúc database của từng service.
- Danh sách API endpoint và request/response.
- Mã lỗi nghiệp vụ.
- Chính sách hủy đơn, đổi trả và hoàn tiền.
- Chính sách đánh giá sản phẩm.
- Chính sách gợi ý và bảo mật dữ liệu cho AI Service.
- Phân quyền chi tiết trong Staff Service.
- Tiêu chí nghiệm thu và test case theo từng workflow.
