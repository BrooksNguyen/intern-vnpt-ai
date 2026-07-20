# PHASE 3: VIẾT PYSPARK ETL DI CHUYỂN DỮ LIỆU (Tuần 5 - 7)

## 📅 Tuần 5: Viết pipeline di chuyển dữ liệu (Cassandra sang ScyllaDB)
* **Mục tiêu:** Viết script PySpark đọc dữ liệu gốc từ Cassandra, tự động tạo trường `bucket_id` mới và đẩy sang ScyllaDB.
* **Nhiệm vụ:**
  1. Sử dụng thư viện PySpark kết nối tới Cassandra đọc DataFrame thô.
  2. Dùng hàm Spark SQL `date_format` và `col` để phân tích cột `timestamp` của tin nhắn, chuyển thành chuỗi định dạng `yyyy-MM` gán vào cột `bucket_id`.
  3. Ghi dữ liệu DataFrame đã biến đổi sang bảng `chat_table_bucketed` thuộc Keyspace `chat_system_target` trong ScyllaDB.
* **Định nghĩa hoàn thành (DoD):**
  - Chạy thành công tập lệnh `pyspark_etl_migration.py`.
  - Sử dụng cqlsh truy vấn ScyllaDB đếm số lượng hàng thấy trùng khớp hoàn toàn 100% với Cassandra.

## 📅 Tuần 6: Tối ưu hóa hiệu năng ETL (Batch size & Concurrency)
* **Mục tiêu:** Tăng tốc độ dịch chuyển dữ liệu lớn bằng cách tối ưu hóa các tham số luồng ghi của Connector.
* **Nhiệm vụ:**
  1. Thêm các cấu hình Spark khi khởi tạo Session để tối ưu tốc độ ghi sang ScyllaDB:
     - `spark.cassandra.output.batch.size.bytes`: Kích thước batch khi gửi lệnh ghi (ví dụ: `65536` bytes).
     - `spark.cassandra.output.concurrent.writes`: Số lượng luồng ghi đồng thời (ví dụ: `5` hoặc `10`).
     - `spark.cassandra.connection.keep_alive_ms`: Duy trì kết nối sống để tránh khởi tạo liên tục.
  2. Theo dõi thời gian chạy (Execution Time) của Spark job trước và sau khi tối ưu để báo cáo hiệu năng.
* **Định nghĩa hoàn thành (DoD):**
  - Các tham số tối ưu hóa ghi được khai báo chuẩn trong code Spark Session.
  - Spark job chạy hoàn thành nhanh hơn đáng kể so với cấu hình mặc định ban đầu.

## 📅 Tuần 7: Lưu trữ dữ liệu lạnh (Archiving sang Parquet)
* **Mục tiêu:** Xây dựng cơ chế lưu trữ lạnh cho các tin nhắn đã quá cũ (ví dụ: trên 6 tháng) ra tệp tin Parquet trên Disk để tiết kiệm dung lượng lưu trữ của database.
* **Nhiệm vụ:**
  1. Viết logic Spark lọc các dòng dữ liệu có `timestamp` nhỏ hơn thời điểm hiện tại 6 tháng.
  2. Ghi tập dữ liệu này xuống ổ đĩa cục bộ dưới định dạng file nén **Parquet** (định dạng lưu trữ dạng cột tối ưu cho Big Data).
     `df.write.mode("overwrite").parquet("data/cold_archive/")`
  3. Phân vùng file Parquet theo `year` và `month` để dễ dàng truy vấn sau này.
* **Định nghĩa hoàn thành (DoD):**
  - Xuất hiện thư mục `data/cold_archive/` chứa các tệp tin `.parquet` được phân chia thư mục theo thời gian.
  - Có thể đọc lại tệp Parquet này lên Spark DataFrame bằng lệnh `spark.read.parquet("data/cold_archive/")` để hiển thị dữ liệu bình thường.
