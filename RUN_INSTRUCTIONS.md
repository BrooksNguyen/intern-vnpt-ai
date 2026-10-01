# 🚀 Hướng dẫn Khởi chạy Hệ thống (Run Instructions)

Tài liệu này cung cấp các bước chi tiết để khởi chạy toàn bộ hệ thống Big Data và Dashboard (từ Phase 0 đến Phase 5) trên môi trường Local.

## 🛠️ 1. Yêu cầu Hệ thống (Prerequisites)
- Đã cài đặt **Docker** và **Docker Compose**.
- Cài đặt **Python 3.9+**.
- Cài đặt các thư viện Python cần thiết:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🏗️ 2. Khởi chạy Cụm Database & Spark (Docker)
Cụm hệ thống sử dụng Docker để chạy Cassandra (Nguồn), ScyllaDB (Đích) và Apache Spark.
Tại thư mục gốc của dự án, mở Terminal và chạy lệnh:
```bash
docker compose up -d
```
Đợi khoảng 30-60 giây để các Container khởi động hoàn tất. Bạn có thể kiểm tra trạng thái bằng lệnh `docker ps` (đảm bảo 3 container `cassandra_source`, `scylla_target` và `pyspark_workspace` đang ở trạng thái **Up**).

---

## ⚡ 3. Chạy Toàn bộ Pipeline Bằng 1-Click (Phase 0 ➔ 4)
Để đơn giản hóa, dự án đã cung cấp một shell script chạy toàn bộ luồng ETL và Phân tích NLP một cách hoàn toàn tự động.

Chạy lệnh sau trên Terminal của máy host:
```bash
bash run_pipeline.sh
```

**Script này sẽ tự động thực hiện các bước:**
1. **Sinh dữ liệu mẫu:** Tạo dữ liệu chat giả lập và đẩy vào Cassandra (Phase 0).
2. **Khởi tạo Database:** Tạo Keyspace và Table (Time-bucketing) trên ScyllaDB (Phase 2).
3. **Thực thi PySpark ETL:** Di dời, biến đổi dữ liệu (tính toán `bucket_id`) và ghi song song từ Cassandra sang ScyllaDB qua container Spark (Phase 3).
4. **Sinh Biểu đồ EDA:** Trực quan hoá dữ liệu sau di dời (Phase 1 & 3).
5. **Chạy Phân tích NLP:** Tiền xử lý văn bản, sinh Keyword, WordCloud và biểu đồ cảm xúc (Phase 4).

> **Lưu ý:** Nếu bạn không muốn bật Docker (hoặc máy yếu), bạn có thể chạy test độc lập tính năng NLP bằng Mock Data qua lệnh: `python3 phase_4_nlp_analysis/nlp_analytics_pipeline.py --offline`

---

## 🖥️ 4. Khởi chạy Backend API & Dashboard (Phase 5)

Sau khi dữ liệu đã được lưu trữ an toàn trong ScyllaDB, bạn có thể khởi chạy giao diện và API.
Bạn cần mở **2 Tab Terminal** mới.

### Terminal 1: Chạy FastAPI Backend
Backend API đóng vai trò truy vấn dữ liệu từ ScyllaDB và hỗ trợ phân trang (Backtracking Pagination).
```bash
uvicorn phase_5_dashboard.api:app --reload --host 0.0.0.0 --port 8000
```
- Truy cập tài liệu API tự sinh (Swagger UI): **http://localhost:8000/docs**

### Terminal 2: Chạy Streamlit Dashboard
Giao diện Web tương tác hiển thị mọi biểu đồ NLP, thông tin cấu trúc cơ sở dữ liệu và công cụ kiểm thử Chat API.
```bash
streamlit run phase_5_dashboard/app.py
```
- Trình duyệt sẽ tự động mở giao diện Dashboard tại: **http://localhost:8501**

---

## 🛑 5. Dọn dẹp và Tắt Hệ thống
Sau khi hoàn thành công việc, để tắt hệ thống và giải phóng tài nguyên RAM/CPU, chạy lệnh:
```bash
docker compose down
```
*(Nếu muốn xóa sạch toàn bộ dữ liệu database để làm lại từ đầu, hãy chạy lệnh `docker compose down -v` để xóa cả Docker Volumes).*
