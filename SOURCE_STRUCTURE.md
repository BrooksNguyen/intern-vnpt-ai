# 📂 Cấu trúc Mã nguồn Dự án (Source Structure)

Dự án được phân chia thành **6 thư mục chính (Phase 0 đến Phase 5)** tương ứng với lộ trình thực tập, kết hợp cùng các file cấu hình và kịch bản (scripts) tự động hóa nằm ở thư mục gốc.

## 🗂️ Thư mục gốc (Root Directory)
- **`docker-compose.yml`**: Tệp cấu hình Docker Compose để khởi chạy cụm dịch vụ gồm Cassandra (Source), ScyllaDB (Target), và PySpark.
- **`run_pipeline.sh`**: Bash script gom toàn bộ quy trình (Sinh mock data ➔ Khởi tạo Schema ➔ Chạy PySpark ETL ➔ Sinh biểu đồ ➔ Chạy NLP) để thực thi chỉ với 1 lệnh (One-click execution).
- **`requirements.txt`**: Danh sách toàn bộ thư viện Python (Dependencies) cần thiết cho dự án.
- **`schema.cql`**: Tệp DDL (Data Definition Language) chứa câu lệnh khởi tạo Keyspace và Bảng trên ScyllaDB (có cấu hình TTL và gc_grace_seconds).
- **`gen_real_charts.py`**: Script kết nối thẳng vào database (Cassandra/ScyllaDB) để trực quan hoá dữ liệu sau khi migrate.

---

## 🗂️ 1. `phase_0_setup/` (Sinh dữ liệu & Khởi tạo)
Chứa các script thiết lập môi trường và sinh dữ liệu giả lập ban đầu.
- **`generate_mock_data.py`**: Sinh ngẫu nhiên dữ liệu chat giả lập, đẩy trực tiếp vào Cassandra. Hỗ trợ tạo hiện tượng "Hot Partition" tại `room_999` để phục vụ bài toán tối ưu hoá.

---

## 🗂️ 2. `phase_1_profiling/` (Khám phá dữ liệu - EDA)
Chứa các notebook và script dùng để phân tích hiện trạng dữ liệu.
- **`eda_plot.py`**: Vẽ biểu đồ từ dữ liệu phân mảnh để phân tích và đánh giá tình trạng tắc nghẽn (bottleneck) ở mức độ partition.

---

## 🗂️ 3. `phase_2_scylla_design/` (Thiết kế CSDL ScyllaDB)
Tối ưu hóa Data Modeling và áp dụng Time-bucketing.
- **`scylla_ddl_manager.py`**: Kết nối và thực thi các câu lệnh CQL tạo bảng mới trên ScyllaDB, áp dụng cấu trúc Primary Key nâng cao: `((room_id, bucket_id), message_id)` để chia nhỏ dữ liệu theo tháng.

---

## 🗂️ 4. `phase_3_pyspark_etl/` (Luồng dữ liệu ETL)
Luồng chuyển đổi và lưu trữ dữ liệu quy mô lớn.
- **`pyspark_etl_migration.py`**: Script PySpark đọc dữ liệu từ Cassandra, xử lý logic thêm cột `bucket_id` dựa trên timestamp, và ghi song song (batch write) sang ScyllaDB.
- **`cold_archiver.py`**: Script PySpark ứng dụng cơ chế *Partition Pruning*, tự động quét và nén các dữ liệu cũ (lạnh) thành định dạng Parquet để đưa vào lưu trữ lạnh (Cold Storage).

---

## 🗂️ 5. `phase_4_nlp_analysis/` (Phân tích Ngôn ngữ Tự nhiên)
Trích xuất thông tin hữu ích từ các tin nhắn chat.
- **`nlp_analytics_pipeline.py`**: Pipeline toàn diện tích hợp thư viện `underthesea` để tiền xử lý văn bản tiếng Việt. Phân tích cảm xúc (Sentiment Analysis), sinh Top 50 Keywords và vẽ biểu đồ WordCloud. Hỗ trợ chế độ `--offline` để sinh dữ liệu mẫu.
- **`stopwords.txt`**: Từ điển các từ dừng (stopwords) tiếng Việt được tuỳ chỉnh cho hệ thống chat.

---

## 🗂️ 6. `phase_5_dashboard/` (API & Giao diện Dashboard)
Trực quan hoá dữ liệu cho người dùng cuối và Mentor.
- **`api.py`**: Dịch vụ Web Backend xây dựng bằng **FastAPI**, cung cấp endpoint `/messages` hỗ trợ phân trang (Pagination) để truy vấn dữ liệu nhanh từ ScyllaDB.
- **`backend_service.py`**: Lõi xử lý logic truy vấn ScyllaDB, nổi bật với thuật toán **Backtracking Pagination** (tự động lùi về các tháng trước nếu bucket hiện tại không đủ dữ liệu).
- **`app.py`**: Giao diện Web Frontend xây dựng bằng **Streamlit**. Tích hợp hiển thị schema, biểu đồ cảm xúc, WordCloud, chat box, và tóm tắt bài học (Lessons Learned) thành 4 Tab trực quan, chuyên nghiệp.

---

## 🗂️ Các thư mục hỗ trợ
- **`Intern_Guide/`**: Toàn bộ tài liệu hướng dẫn nghiệp vụ và yêu cầu bài toán từ Mentor cho các tuần thực tập.
- **`overleaf_report/`**: Mã nguồn LaTeX của báo cáo chuyên đề thực tập cuối kỳ, đồng bộ với các kết quả xuất ra (ảnh, bảng biểu).
