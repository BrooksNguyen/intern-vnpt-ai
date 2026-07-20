# PHASE 2: THIẾT KẾ LẠI CƠ SỞ DỮ LIỆU TRÊN SCYLLADB (Tuần 3 - 4)

## 📅 Tuần 3: Khắc phục Hot Partition bằng Time Bucketing
* **Mục tiêu:** Thiết kế lại cấu trúc bảng để phân tán dữ liệu của các phòng chat khổng lồ (như `room_999`) sang nhiều phân vùng vật lý khác nhau.
* **Nhiệm vụ:**
  1. Thay vì sử dụng Khóa phân vùng (Partition Key) duy nhất là `room_id` làm dữ liệu bị dồn vào một node duy nhất, em cần thiết kế khóa phân vùng phức hợp: `((room_id, bucket_id), message_id)`.
  2. Cột `bucket_id` là một chuỗi văn bản đại diện cho khoảng thời gian (ví dụ: `YYYY-MM` theo định dạng Năm-Tháng). Khi đó, dữ liệu của cùng một phòng chat lớn sẽ được chia nhỏ ra theo từng tháng, tự động phân phối đều qua các node trong cụm.
  3. Cột `message_id` là định dạng `timeuuid` làm Khóa sắp xếp (Clustering Key) để tin nhắn tự sắp xếp theo thời gian mới nhất lên đầu (`WITH CLUSTERING ORDER BY (message_id DESC)`).
* **Định nghĩa hoàn thành (DoD):**
  - Chạy thành công tập lệnh `test_scylla_conn.py` để khởi tạo keyspace `chat_system_target` và tạo bảng mới `chat_table_bucketed` trong container ScyllaDB.
  - Sử dụng CQL Shell (`cqlsh`) truy cập ScyllaDB check schema của bảng mới xem đúng cấu trúc composite partition key chưa.

## 📅 Tuần 4: Cấu hình Compaction Strategy và TTL cho ScyllaDB
* **Mục tiêu:** Cấu hình chiến lược nén dữ liệu tối ưu cho dữ liệu dạng chuỗi thời gian (Timeseries Data) và thiết lập thời gian tự động xóa tin nhắn rác (TTL).
* **Nhiệm vụ:**
  1. Với dữ liệu chat là dữ liệu ghi liên tục theo thời gian, chiến lược nén tối ưu nhất là **Time Window Compaction Strategy (TWCS)** thay vì chiến lược mặc định Size Tiered.
  2. Thực hiện khai báo TWCS cho bảng khi khởi tạo với các tham số:
     `compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_unit': 'DAYS', 'compaction_window_size': 1}`.
  3. Tìm hiểu cách thiết lập thuộc tính **TTL (Time-To-Live)** để tự động hết hạn và xóa bỏ dữ liệu tin nhắn cũ sau một thời gian (ví dụ: 1 năm = 31536000 giây) để tránh tràn bộ nhớ.
* **Định nghĩa hoàn thành (DoD):**
  - Đưa được cấu hình TWCS vào câu lệnh khởi tạo bảng ScyllaDB thành công.
  - Chạy lệnh `DESCRIBE TABLE chat_table_bucketed;` trong ScyllaDB cqlsh thấy hiển thị đúng chiến lược compaction TWCS đã cấu hình.
