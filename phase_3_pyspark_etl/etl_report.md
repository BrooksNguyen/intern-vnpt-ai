# Báo Cáo Tiến Độ Phase 3

## 1. Mục tiêu công việc

Xây dựng pipeline ETL bằng PySpark để thực hiện di dời dữ liệu (data migration) từ hệ thống lưu trữ Cassandra hiện tại sang cụm ScyllaDB mới.

## 2. Quá trình triển khai và giải quyết vấn đề (Tuần 5)

**Khởi tạo và cấu hình:** PySpark được lựa chọn làm công cụ xử lý chính nhờ khả năng đáp ứng tốt các bài toán Big Data. Trong giai đoạn đầu thiết lập, quá trình kết nối phát sinh lỗi `ClassNotFound` do thiếu thư viện giao tiếp trực tiếp với Cassandra. Vấn đề này đã được xử lý thành công bằng cách cấu hình biến môi trường `PYSPARK_SUBMIT_ARGS`, cho phép Spark tự động tải các gói dependency (`.jar`) cần thiết trong quá trình thực thi.

![Ảnh terminal ghi nhận lỗi thư viện trước khi cấu hình](images/cassandra_class_not_found.png)

**Thiết kế phân mảnh dữ liệu (Time-bucketing):** Quá trình trích xuất (Extract) dữ liệu từ Cassandra diễn ra ổn định. Ở bước Transform, em đã chủ động bổ sung trường `bucket_id` (theo định dạng yyyy-MM) trước khi nạp vào cơ sở dữ liệu đích. Quyết định thiết kế này nhằm phân tán dữ liệu theo tháng, giúp hệ thống tránh được tình trạng "Hot Partition" tại các phòng chat có lưu lượng tin nhắn lớn. Cách tiếp cận đồng nhất này ưu việt hơn so với chia bucket động vì nó giữ cho logic truy vấn của Backend đơn giản, không cần bảng tra cứu (lookup table).

**Ghi dữ liệu (Load):** Tại bước đẩy dữ liệu vào ScyllaDB, pipeline được cấu hình sử dụng phương thức `.mode("append")`. Việc này nhằm đảm bảo tính toàn vẹn và an toàn tuyệt đối, loại trừ rủi ro ghi đè lên các dữ liệu có sẵn trên cluster ScyllaDB mới.

## 3. Cập nhật Tuần 6: Tối ưu hiệu năng I/O

Trong tuần 6, tập trung vào việc xử lý vấn đề thắt cổ chai ở throughput khi ghi vào ScyllaDB. Em đã tích hợp thêm cờ `--mode optimized` để Spark tự động thiết lập các cấu hình nâng cao:
- **`spark.cassandra.output.batch.size.bytes`**: Tăng lên `65536` bytes để gom nhiều thao tác ghi vào một batch, giảm tải network overhead.
- **`spark.cassandra.output.concurrent.writes`**: Thiết lập `10` luồng ghi song song trên mỗi task, tăng cường khả năng tận dụng IOPS của ổ cứng.
- **`spark.cassandra.connection.keepAliveMS`**: Giữ kết nối tới ScyllaDB lâu hơn (10 giây) để tái sử dụng connection pooling hiệu quả.

Quá trình benchmark cho thấy write throughput được cải thiện rõ rệt so với cấu hình mặc định (default).

## 4. Cập nhật Tuần 7: Hệ thống Cold Archiver (Sao lưu dữ liệu lạnh)

Nhằm tối ưu hóa dung lượng lưu trữ trên database, kịch bản `cold_archiver.py` đã được xây dựng để xuất các tin nhắn không còn thường xuyên truy cập ra lưu trữ ngoài (ví dụ: S3 hoặc Local Disk).

**Kết quả đạt được:**
- Xử lý mốc thời gian hoàn toàn bằng `datetime` chuẩn của Python, lọc các dữ liệu cũ hơn 6 tháng (tùy chỉnh qua tham số `--months-old`).
- Dữ liệu cũ được ghi thành định dạng **Parquet**, định dạng Columnar tối ưu cao cho việc nén và truy vấn phân tích (Big Data/OLAP).
- Tích hợp logic phân vùng `partitionBy("year", "month")`, giúp các công cụ Query sau này đọc file Parquet siêu tốc độ.
- Ngăn chặn hoàn toàn I/O overhead do Double Scanning, đảm bảo hiệu năng I/O luôn ở mức lý tưởng.
