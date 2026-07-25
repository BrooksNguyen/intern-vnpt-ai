# BÁO CÁO PHÂN TÍCH THIẾT KẾ CƠ SỞ DỮ LIỆU SCYLLADB

Tài liệu này trình bày phân tích thiết kế cơ sở dữ liệu ScyllaDB (Giai đoạn 2) nhằm giải quyết triệt để lỗi Hot Partition của hệ thống cũ.

---

## 1. Lý thuyết Token-Aware Routing
- **Khái niệm:** Trong cụm ScyllaDB/Cassandra, dữ liệu được băm (hashing) thành các token thông qua thuật toán Murmur3 để quyết định xem bản ghi đó sẽ nằm ở node vật lý nào.
- **Token-Aware Driver:** Khi ứng dụng backend gửi một câu truy vấn, nếu driver được cấu hình `TokenAware`, nó sẽ tự tính toán token của khóa phân vùng (Partition Key) và gửi lệnh truy vấn trực tiếp đến đúng Node lưu trữ dữ liệu đó (Replica Node), thay vì gửi qua một Node trung gian (Coordinator Node).
- **Ý nghĩa:** Tiết kiệm băng thông mạng trong cụm, giảm độ trễ (latency) của câu truy vấn từ O(N) xuống O(1) và loại bỏ hiện tượng nút cổ chai tại node điều phối.

---

## 2. Thiết kế Schema chống ALLOW FILTERING & Hot Partition

### Vấn đề của Schema cũ:
- Khóa chính là `PRIMARY KEY (room_id, message_id)`.
- Khi phòng `room_999` có số lượng tin nhắn quá lớn (hàng triệu dòng), toàn bộ dữ liệu sẽ dồn về 1 Partition vật lý duy nhất. Điều này khiến Node lưu trữ Partition đó bị quá tải (Hot Partition), dẫn đến treo cụm.
- Nếu muốn tìm tin nhắn theo loại hoặc thiết bị mà không có trong khóa phân vùng, lập trình viên buộc phải thêm `ALLOW FILTERING`, khiến hệ thống quét toàn bộ database, làm giảm hiệu năng nghiêm trọng.

### Giải pháp tối ưu (Time Bucketing):
- Phân rã dữ liệu của một phòng chat bằng cách đưa thêm thời gian vào khóa phân vùng tạo thành Khóa phân vùng phức hợp (Composite Partition Key): `((room_id, bucket_id), message_id)`.
- Trong đó, `bucket_id` có giá trị là năm-tháng gửi tin nhắn dạng `YYYY-MM` (ví dụ: `2026-07`).
- Dữ liệu của cùng một phòng chat lớn sẽ được chia nhỏ ra theo tháng và nằm ở các partition khác nhau trên các node vật lý khác nhau, san đều tải cho toàn cụm.

---

## 3. Các câu truy vấn Backend mẫu (CQL)

### Truy vấn 1: Lấy 50 tin nhắn mới nhất của phòng chat (Room A) trong tháng hiện tại
```sql
SELECT room_id, bucket_id, message_id, user_id, content, msg_type, device, is_edited, timestamp 
FROM chat_system_target.chat_table_bucketed 
WHERE room_id = 'room_1' AND bucket_id = '2026-07' 
LIMIT 50;
```
*(Do clustering key `message_id` được sắp xếp giảm dần `DESC`, câu lệnh này sẽ trả về 50 tin nhắn mới nhất ngay lập tức mà không cần quét toàn bảng).*

### Truy vấn 2: Phân trang - User vuốt ngược lên để load các tin nhắn cũ hơn
```sql
SELECT room_id, bucket_id, message_id, user_id, content, msg_type, device, is_edited, timestamp 
FROM chat_system_target.chat_table_bucketed 
WHERE room_id = 'room_1' 
  AND bucket_id = '2026-07' 
  AND message_id < 6ff1b35a-8405-11f1-8e64-af4db1424c6c 
LIMIT 50;
```
*(Sử dụng toán tử nhỏ hơn `< message_id_cũ_nhất` để lấy tiếp các tin nhắn tiếp theo trong cùng phân mảnh thời gian).*

---

## 4. Chiến lược tự động dọn dẹp dữ liệu (TWCS, TTL và Tombstone)

- **TWCS (Time Window Compaction Strategy):** ScyllaDB sẽ tự động gom các tệp tin lưu trữ vật lý (SSTables) theo các khoảng thời gian (Window) bằng nhau (ví dụ: 1 ngày). Khi dữ liệu của một ngày cũ bị xóa hoặc hết hạn, toàn bộ file SSTable của ngày đó sẽ được thu hồi đĩa một cách nhanh chóng mà không tốn tài nguyên CPU để compaction chéo.
- **Default TTL:** Bảng được cấu hình `default_time_to_live = 15552000` (180 ngày). Các tin nhắn cũ hơn 6 tháng sẽ tự động biến mất để giải phóng tài nguyên.
- **Tombstone & gc_grace_seconds:** Khi một bản ghi bị xóa hoặc hết hạn TTL, ScyllaDB sẽ đánh dấu nó bằng một thẻ gọi là **Tombstone**. Bản ghi này chưa thực sự bị xóa khỏi ổ đĩa mà được giữ lại trong khoảng thời gian `gc_grace_seconds` (mặc định là 10 ngày) để đảm bảo đồng bộ hóa trạng thái xóa đến tất cả các Node sao lưu (Replicas) trước khi bị xóa vật lý hoàn toàn.
