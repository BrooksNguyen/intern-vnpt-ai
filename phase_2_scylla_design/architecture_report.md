# Phân tích thiết kế ScyllaDB

Note lại mấy cái mình tìm hiểu được về ScyllaDB trong quá trình redesign schema cho hệ thống chat.

---

## Token-Aware Routing

ScyllaDB/Cassandra hash partition key bằng Murmur3 rồi phân bổ data vào các node theo token range. Nếu driver client cấu hình `TokenAware` thì nó tự tính token và gửi request thẳng tới đúng node chứa data, bỏ qua coordinator node => giảm latency đáng kể.

## Vấn đề schema cũ

Schema cũ dùng `PRIMARY KEY (room_id, message_id)` nên toàn bộ tin nhắn 1 room dồn vào 1 partition. Room nào chat nhiều (room_999 chẳng hạn) thì partition đó phình to => node bị quá tải = Hot Partition.

Muốn query kiểu filter theo `msg_type` hay `device` mà ko có trong partition key thì phải `ALLOW FILTERING` => full scan, chậm kinh khủng.

## Giải pháp: Composite Partition Key + Time Bucketing

Thêm `bucket_id` (format `YYYY-MM`) vào partition key:

```
PRIMARY KEY ((room_id, bucket_id), message_id)
```

Room lớn sẽ tự động chia nhỏ theo tháng, mỗi tháng 1 partition riêng => phân tải đều.

## Query mẫu cho Backend

**Lấy 50 tin mới nhất:**
```sql
SELECT * FROM chat_system_target.chat_table_bucketed
WHERE room_id = 'room_1' AND bucket_id = '2026-07'
LIMIT 50;
```

**Phân trang (user vuốt lên xem tin cũ):**
```sql
SELECT * FROM chat_system_target.chat_table_bucketed
WHERE room_id = 'room_1' AND bucket_id = '2026-07'
  AND message_id < 6ff1b35a-8405-11f1-8e64-af4db1424c6c
LIMIT 50;
```

Clustering key `message_id DESC` nên mặc định trả tin mới nhất trước, ko cần sort.

## TWCS, TTL, Tombstone

- **TWCS**: gom SSTable theo time window (1 ngày). Khi data cũ hết hạn thì drop cả file luôn, ko tốn CPU compaction chéo.
- **TTL**: set `default_time_to_live = 2592000` (30 ngày). ScyllaDB giới hạn `twcs_max_window_count = 50` nên TTL / window_size phải < 50.
- **Tombstone**: bản ghi bị xóa/hết TTL sẽ được đánh dấu tombstone, giữ lại `gc_grace_seconds` (default 10 ngày) để sync giữa các replica rồi mới xóa vật lý.
