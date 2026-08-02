# Báo Cáo Tiến Độ Phase 3 (Tuần 5)

## 1. Mục tiêu công việc

Xây dựng pipeline ETL bằng PySpark để thực hiện di dời dữ liệu (data migration) từ hệ thống lưu trữ Cassandra hiện tại sang cụm ScyllaDB mới.

## 2. Quá trình triển khai và giải quyết vấn đề

**Khởi tạo và cấu hình:** PySpark được lựa chọn làm công cụ xử lý chính nhờ khả năng đáp ứng tốt các bài toán Big Data. Trong giai đoạn đầu thiết lập, quá trình kết nối phát sinh lỗi `ClassNotFound` do thiếu thư viện giao tiếp trực tiếp với Cassandra. Vấn đề này đã được xử lý thành công bằng cách cấu hình biến môi trường `PYSPARK_SUBMIT_ARGS`, cho phép Spark tự động tải các gói dependency (`.jar`) cần thiết trong quá trình thực thi.

![Ảnh terminal ghi nhận lỗi thư viện trước khi cấu hình](images/cassandra_class_not_found.png)

**Thiết kế phân mảnh dữ liệu (Time-bucketing):** Quá trình trích xuất (Extract) dữ liệu từ Cassandra diễn ra ổn định. Ở bước Transform, em đã chủ động bổ sung trường `bucket_id` (theo định dạng yyyy-MM) trước khi nạp vào cơ sở dữ liệu đích. Quyết định thiết kế này nhằm phân tán dữ liệu theo tháng, giúp hệ thống tránh được tình trạng "Hot Partition" tại các phòng chat có lưu lượng tin nhắn lớn.

**Đánh giá hạn chế (Trade-off):** Mặc dù giải quyết được rủi ro thắt cổ chai, phương pháp bucketing mặc định này sẽ gây ra sự phân mảnh dư thừa đối với các phòng chat ít tương tác, có nguy cơ làm tăng chi phí truy vấn (query) sau này. Vấn đề này đã được note lại (`FIXME`) trong mã nguồn để tiếp tục tối ưu hóa. Hướng giải quyết dự kiến là áp dụng logic động: chỉ kích hoạt chia bucket cho các phòng chat vượt ngưỡng 1000 tin nhắn.

**Ghi dữ liệu (Load):** Tại bước đẩy dữ liệu vào ScyllaDB, pipeline được cấu hình sử dụng phương thức `.mode("append")`. Việc này nhằm đảm bảo tính toàn vẹn và an toàn tuyệt đối, loại trừ rủi ro ghi đè lên các dữ liệu có sẵn trên cluster ScyllaDB mới.

## 3. Kết quả sơ bộ và Kế hoạch Tuần 6

**Kết quả:** Pipeline ETL cơ bản đã vận hành thành công. Quá trình kiểm tra chéo cho thấy toàn bộ dữ liệu đã được migrate đầy đủ sang hệ thống mới, không xảy ra tình trạng thất thoát bản ghi.

**Kế hoạch Tuần 6:** Dù luồng xử lý đã đảm bảo tính chính xác về mặt logic, hiệu năng và tốc độ ghi (write throughput) hiện tại vẫn chưa đạt mức tối ưu. Trong tuần tiếp theo, em sẽ tiến hành benchmark và tinh chỉnh các tham số cấu hình I/O của Spark (ví dụ: batch size, concurrent writes) nhằm tối đa hóa tốc độ ghi vào ScyllaDB.
