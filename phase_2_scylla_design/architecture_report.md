# Báo Cáo Thiết Kế Kiến Trúc ScyllaDB

Tài liệu tóm tắt các quyết định thiết kế khi chuyển đổi cơ sở dữ liệu từ Cassandra sang ScyllaDB.

## 1. Token-Aware Routing
ScyllaDB và Cassandra phân bổ dữ liệu dựa trên hàm băm (Murmur3) của partition key. Việc cấu hình `TokenAware` trên client driver giúp gửi truy vấn trực tiếp đến Node chứa dữ liệu, bỏ qua Coordinator Node, từ đó giảm độ trễ (latency).

## 2. Vấn đề của Kiến trúc cũ
- **Schema cũ:** `PRIMARY KEY (room_id, message_id)`. Toàn bộ dữ liệu của một phòng chat lưu trên một partition duy nhất.
- **Vấn đề:** Các phòng chat lớn (như `room_999`) gây ra hiện tượng Hot Partition, làm quá tải một số Node cụ thể. Việc truy vấn theo các trường phụ (`msg_type`, `device`) yêu cầu `ALLOW FILTERING`, dẫn đến full scan và giảm hiệu năng.

## 3. Giải pháp: Composite Partition Key & Time Bucketing
Cấu trúc khóa chính được thiết kế lại, bổ sung trường `bucket_id` (định dạng `YYYY-MM`):

```sql
PRIMARY KEY ((room_id, bucket_id), message_id)
```

**Ưu điểm:** Dữ liệu của các phòng chat lớn tự động phân tách theo từng tháng vào các partition khác nhau, đảm bảo phân bổ tải trọng đồng đều trên toàn cụm (cluster).

## 4. Các Mẫu Truy Vấn Hỗ trợ Backend

**Lấy 50 tin nhắn mới nhất:**
```sql
SELECT * FROM chat_system_target.chat_table_bucketed
WHERE room_id = 'room_1' AND bucket_id = '2026-07'
LIMIT 50;
```

**Truy xuất phân trang lịch sử tin nhắn:**
```sql
SELECT * FROM chat_system_target.chat_table_bucketed
WHERE room_id = 'room_1' AND bucket_id = '2026-07'
  AND message_id < 6ff1b35a-8405-11f1-8e64-af4db1424c6c
LIMIT 50;
```
*(Khóa sắp xếp `message_id DESC` đảm bảo kết quả luôn trả về tin nhắn mới nhất trước).*

## 5. Quản Lý Vòng Đời Dữ Liệu
- **TimeWindowCompactionStrategy (TWCS):** Nhóm các SSTable theo khung thời gian (ví dụ: 1 ngày). Tối ưu hóa việc xóa dữ liệu cũ, giảm tải CPU so với nén chéo (cross-compaction).
- **Time-To-Live (TTL):** Thiết lập `default_time_to_live = 2592000` (30 ngày) để tự động xóa dữ liệu hết hạn. Tỷ lệ TTL/window được duy trì < 50 theo giới hạn của ScyllaDB.
- **Tombstone:** Các bản ghi hết hạn TTL sẽ được đánh dấu (tombstone) và giữ lại trong `gc_grace_seconds` (mặc định 10 ngày) để hoàn tất đồng bộ (sync) giữa các replica trước khi xóa vật lý.
