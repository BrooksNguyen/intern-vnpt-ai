# Dự án Thực tập VNPT AI - Tối ưu hóa Dữ liệu Hệ thống Chat

## Giới thiệu

Đây là dự án thực hiện trong quá trình thực tập tại VNPT AI với mục tiêu xây dựng, tối ưu hóa và phân tích dữ liệu cho một hệ thống lưu trữ tin nhắn chat quy mô lớn. Trọng tâm của dự án là việc di dời dữ liệu (ETL) từ Apache Cassandra sang ScyllaDB nhằm giải quyết bài toán Hot Partition, thiết lập luồng xử lý ngôn ngữ tự nhiên (NLP) trên tiếng Việt, và xây dựng Dashboard báo cáo trực quan.

Dự án được chia làm **6 Giai đoạn (Phases)** tương ứng với lộ trình thực tập.

---

## Lộ trình Dự án (6 Phases)

- **Phase 0: Thiết lập Môi trường Phát triển (Environment Setup)**
  Triển khai hệ thống Big Data cục bộ bằng Docker Compose bao gồm: Apache Cassandra (nguồn), ScyllaDB (đích) và PySpark. Sinh dữ liệu giả lập (Mock Data) tạo ra hiện tượng Hot Partition để thử nghiệm.

- **Phase 1: Phân tích Dữ liệu Khám phá (Data Profiling & EDA)**
  Truy vấn và đánh giá dữ liệu trên Cassandra. Phát hiện phòng chat `room_999` chiếm đa số lượng tin nhắn, dẫn tới mất cân bằng tải (Hot Partition).

- **Phase 2: Thiết kế Kiến trúc ScyllaDB (ScyllaDB Design)**
  Thiết kế lại schema CSDL trên ScyllaDB. Chuyển đổi Partition Key từ `room_id` sang `(room_id, bucket_id)` để phân mảnh dữ liệu theo tháng (Time-bucketing), giải quyết dứt điểm vấn đề Hot Partition.

- **Phase 3: Xây dựng Pipeline ETL bằng PySpark (PySpark ETL)**
  Thiết lập luồng ETL chuyển dữ liệu từ Cassandra sang ScyllaDB. Tối ưu hóa cấu hình Spark I/O (batch size, concurrent writes) và xây dựng Cold Archiver lưu trữ dữ liệu cũ ra định dạng Parquet.

- **Phase 4: Phân tích NLP trên Tin nhắn Chat (NLP Analysis)**
  Tiền xử lý văn bản tiếng Việt (Text Preprocessing) sử dụng thư viện `underthesea` (tách từ, loại bỏ stopwords, bảo vệ emoticon). Phân tích cảm xúc (Sentiment Analysis) và trực quan hóa WordCloud để tìm ra xu hướng tương tác của người dùng. *(Đang triển khai đến phần Tiền xử lý)*

- **Phase 5: Xây dựng API và Dashboard (Streamlit API)**
  *(Dự kiến)* Xây dựng API cung cấp dữ liệu bằng FastAPI (có hỗ trợ phân trang) và xây dựng Dashboard báo cáo theo thời gian thực bằng Streamlit hiển thị các chỉ số phân tích NLP.

---

## Kiến trúc Hệ thống

```text
             Dữ liệu Chat (Mock)
                    │
                    ▼
           Apache Cassandra (Phase 0-1)
                    │
                    ▼
              PySpark ETL (Phase 3)
       - Xử lý Time Bucketing (bucket_id)
       - Lưu trữ lạnh (Cold Archiver -> Parquet)
                    │
                    ▼
               ScyllaDB (Phase 2)
                    │
                    ▼
             Phân tích NLP (Phase 4)
       - Tiền xử lý văn bản (underthesea)
       - Sentiment Analysis & WordCloud
                    │
                    ▼
   FastAPI & Dashboard Streamlit (Phase 5)
```

---

## Công nghệ sử dụng

- **Ngôn ngữ & Thư viện:** Python 3.x, Pandas, Matplotlib, WordCloud, underthesea (NLP).
- **Cơ sở dữ liệu:** Apache Cassandra (v4.1), ScyllaDB (latest).
- **Xử lý Big Data:** Apache Spark (PySpark 3.4.x).
- **Hạ tầng & Triển khai:** Docker, Docker Compose.
- **Backend & Dashboard:** FastAPI, Streamlit.

---

## Hướng dẫn khởi chạy cục bộ

### 1. Khởi động Cụm Docker
```bash
docker compose up -d
```
Xác nhận 3 container: `cassandra_source`, `scylla_target` và `pyspark_workspace` đang chạy.

### 2. Sinh dữ liệu giả lập (Phase 0)
```bash
docker cp phase_0_setup/generate_mock_data.py pyspark_workspace:/home/jovyan/work/
docker exec -it pyspark_workspace python /home/jovyan/work/generate_mock_data.py
```

### 3. Thiết lập Schema ScyllaDB (Phase 2)
```bash
docker cp scripts/test_scylla_conn.py pyspark_workspace:/home/jovyan/work/
docker exec -it pyspark_workspace python /home/jovyan/work/test_scylla_conn.py
```

### 4. Chạy PySpark ETL (Phase 3)
Chạy script để migrate dữ liệu và tự động gán cột `bucket_id`:
```bash
docker cp phase_3_pyspark_etl/pyspark_etl_migration.py pyspark_workspace:/home/jovyan/work/
docker exec -it -e PYTHONPATH="/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip" pyspark_workspace python /home/jovyan/work/pyspark_etl_migration.py
```

---

## Troubleshooting (Lỗi thường gặp)

1. **Lỗi `ModuleNotFoundError: No module named 'pyspark'`**
   - Cần export biến `PYTHONPATH` khi chạy script `.py` trực tiếp trong container Jupyter (như lệnh ở Bước 4).

2. **Lỗi `SimpleStrategy doesn't support tablet replication` khi tạo Keyspace ở ScyllaDB**
   - Chuyển sang sử dụng `NetworkTopologyStrategy` kết hợp datacenter `'datacenter1'` thay cho `SimpleStrategy`.
