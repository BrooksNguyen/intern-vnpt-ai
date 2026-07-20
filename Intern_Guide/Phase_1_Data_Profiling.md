# PHASE 1: DATA PROFILING & KHÁM PHÁ (Tuần 1 - 2)

## 📅 Tuần 1: Khởi tạo môi trường & Data Ingestion
* **Mục tiêu:** Có một hệ thống database local chạy ổn định và chứa dữ liệu mẫu để bắt đầu làm việc.
* **Nhiệm vụ:**
  1. Đọc kỹ hướng dẫn ở file `Phase_0_Environment_Setup.md` và sử dụng file `docker-compose.yml` có sẵn để start các container (Cassandra, ScyllaDB, Jupyter Notebook).
  2. Đảm bảo các container chạy ổn định và không bị lỗi thoát đột ngột.
  3. Sử dụng script `generate_mock_data.py` trong thư mục `scripts` để tự động tạo Keyspace `chat_system` và bảng `chat_table` trên Cassandra rồi chèn dữ liệu mẫu.
* **Định nghĩa hoàn thành (DoD):**
  - Cả 3 container hiển thị màu xanh lá cây trong Docker Desktop.
  - Có thể sử dụng công cụ DBeaver hoặc cqlsh kết nối vào Cassandra cổng `9042`.
  - Lệnh truy vấn `SELECT COUNT(*) FROM chat_table;` trong CQL shell trả về đúng số lượng bản ghi đã sinh.

## 📅 Tuần 2: Exploratory Data Analysis (EDA) với PySpark
* **Mục tiêu:** Nắm được bức tranh tổng thể về phân phối dữ liệu (Data Distribution) và phát hiện ra lỗi thiết kế cốt lõi của hệ thống cũ (Hot Partition).
* **Nhiệm vụ:**
  1. Mở Jupyter Notebook, cấu hình gói `spark-cassandra-connector` và khởi chạy SparkSession.
  2. Đọc bảng `chat_table` từ Cassandra vào Spark DataFrame.
  3. Kiểm tra chất lượng dữ liệu: Đếm số dòng trống (null) trên từng cột, xác định khoảng thời gian của tin nhắn (giá trị timestamp Min/Max).
  4. Thực hiện Group By theo cột `room_id` để đếm số lượng tin nhắn trong từng phòng chat. Từ đó lọc ra các phòng chat chứa số lượng tin nhắn cực lớn, vượt trội so với các phòng thông thường.
* **Định nghĩa hoàn thành (DoD):**
  - File notebook chạy trơn tru từ trên xuống dưới mà không báo lỗi.
  - Vẽ được biểu đồ cột (Bar chart) hiển thị Top 10 phòng chat có nhiều tin nhắn nhất sử dụng thư viện `matplotlib` hoặc `seaborn`.
  - Chỉ ra chính xác Room ID nào đang chịu lượng tải tin nhắn khổng lồ (tác nhân gây ra hiện tượng **Hot Partition** làm treo hệ thống).
