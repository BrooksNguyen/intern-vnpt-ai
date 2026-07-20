# Dự án Thực tập VNPT AI - Tối ưu hóa Dữ liệu Hệ thống Chat

## Giới thiệu

Đây là dự án thực hiện trong quá trình thực tập tại VNPT AI với mục tiêu tìm hiểu và tối ưu hệ thống lưu trữ dữ liệu chat quy mô lớn. Dự án tập trung vào việc di chuyển dữ liệu từ Apache Cassandra sang ScyllaDB, xây dựng pipeline ETL bằng PySpark và thực hiện một số phân tích dữ liệu, NLP trên dữ liệu tin nhắn.

---

## Mục tiêu

- Xây dựng môi trường Big Data bằng Docker.
- Mô phỏng dữ liệu hệ thống chat.
- Phân tích các vấn đề hiệu năng của Apache Cassandra.
- Giảm hiện tượng Hot Partition bằng cách thiết kế lại schema.
- Xây dựng pipeline ETL bằng PySpark để di chuyển dữ liệu.
- Phân tích dữ liệu tin nhắn bằng các kỹ thuật NLP.
- Trực quan hóa dữ liệu bằng Streamlit.

---

## Công nghệ sử dụng

- Python
- Apache Cassandra
- ScyllaDB
- Apache Spark (PySpark)
- Docker & Docker Compose
- Pandas
- NLTK / SpaCy
- Streamlit

---

## Kiến trúc hệ thống

```text
             Dữ liệu giả lập
                    │
                    ▼
          Apache Cassandra
                    │
                    ▼
             PySpark ETL
       - Làm sạch dữ liệu
       - Time Bucketing
       - Chuyển đổi dữ liệu
                    │
                    ▼
                ScyllaDB
                    │
                    ▼
             Phân tích NLP
                    │
                    ▼
          Dashboard Streamlit
```

---

## Cấu trúc dự án

```text
vnpt-ai-internship/
├── docker-compose.yml        # Cấu hình Cassandra, ScyllaDB và PySpark container
├── README.md                 # Tài liệu hướng dẫn chạy và sửa lỗi
├── scripts/
│   ├── generate_mock_data.py # Sinh dữ liệu chat giả lập vào Cassandra (tạo hot partition room_999)
│   ├── test_pyspark_conn.py  # Test kết nối Spark với Cassandra
│   ├── test_scylla_conn.py   # Test kết nối ScyllaDB và tạo schema đích (phân mảnh tránh hot partition)
│   └── pyspark_etl_migration.py # Pipeline ETL đọc Cassandra -> biến đổi -> ghi ScyllaDB
└── notebooks/
    └── 0_spark_connection_test.ipynb # File kiểm tra kết nối trên Jupyter Notebook
```

---

## Hướng dẫn chạy dự án

### Bước 1. Khởi động Docker
Đảm bảo Docker Desktop đã được bật, chạy lệnh sau ở root folder:
```bash
docker compose up -d
```
Xác nhận cả 3 container `cassandra_source`, `scylla_target` và `pyspark_workspace` đang chạy bằng `docker ps`.

### Bước 2. Sinh dữ liệu giả lập (Cassandra)
Sao chép tập lệnh sinh dữ liệu vào container PySpark và thực thi:
```bash
docker cp scripts/generate_mock_data.py pyspark_workspace:/home/jovyan/work/generate_mock_data.py
docker exec -it pyspark_workspace python /home/jovyan/work/generate_mock_data.py
```
Script sẽ tự động khởi tạo keyspace `chat_system` và bảng `chat_table`, nạp các tin nhắn chat giả lập (trong đó room_999 chứa 2000 tin nhắn tạo ra **Hot Partition**).

### Bước 3. Khởi tạo schema đích trên ScyllaDB
Tạo keyspace và bảng đích được thiết kế lại theo chiến lược tránh Hot Partition:
```bash
docker cp scripts/test_scylla_conn.py pyspark_workspace:/home/jovyan/work/test_scylla_conn.py
docker exec -it pyspark_workspace python /home/jovyan/work/test_scylla_conn.py
```

### Bước 4. Chạy PySpark ETL di chuyển dữ liệu
Thực thi di chuyển dữ liệu từ Cassandra sang ScyllaDB, tự động gán cột `bucket_id` theo dạng `yyyy-MM` dựa trên timestamp tin nhắn:
```bash
docker cp scripts/pyspark_etl_migration.py pyspark_workspace:/home/jovyan/work/pyspark_etl_migration.py
docker exec -it -e PYTHONPATH="/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip" pyspark_workspace python /home/jovyan/work/pyspark_etl_migration.py
```

---

## Thiết kế cơ sở dữ liệu

### Thiết kế ban đầu (Cassandra)
```text
Partition Key: room_id
Clustering Key: message_id
```
**Nhược điểm:** Dễ gặp vấn đề Hot Partition nếu một phòng chat có số lượng tin nhắn quá lớn (như phòng chat tổng của công ty hoặc nhóm bot tự động), dẫn đến kích thước partition vượt giới hạn khuyến nghị, truy vấn bị chậm và dữ liệu phân bố không đều giữa các node.

### Thiết kế sau khi tối ưu (ScyllaDB)
```text
Partition Key: (room_id, bucket_id)
Clustering Key: message_id
```
**Ưu điểm:** Bổ sung `bucket_id` (được định dạng theo `YYYY-MM` từ thời gian gửi tin nhắn) giúp chia nhỏ partition lớn theo thời gian, giảm tải cho từng node và đảm bảo khả năng mở rộng tốt hơn.

---

## Lỗi thường gặp và cách xử lý (Troubleshooting)

### 1. Lỗi `ModuleNotFoundError: No module named 'pyspark'`
* **Nguyên nhân:** Khi chạy file `.py` trực tiếp bằng lệnh `python` bên trong container `pyspark_workspace`, Python (conda) không biết đường dẫn đến thư viện PySpark tích hợp sẵn trong thư mục Spark của container.
* **Cách khắc phục:** Cần export biến môi trường `PYTHONPATH` trước khi chạy hoặc truyền trực tiếp vào lệnh thực thi như sau:
  ```bash
  docker exec -it -e PYTHONPATH="/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip" pyspark_workspace python <tên_script>.py
  ```

### 2. Lỗi `SimpleStrategy doesn't support tablet replication` khi tạo keyspace ở ScyllaDB
* **Nguyên nhân:** Phiên bản ScyllaDB mới sử dụng cơ chế lưu trữ dạng tablet, không còn hỗ trợ `SimpleStrategy` khi khởi tạo keyspace.
* **Cách khắc phục:** Sửa câu lệnh CQL tạo keyspace, chuyển sang sử dụng `NetworkTopologyStrategy` kết hợp với datacenter mặc định là `'datacenter1'`:
  ```sql
  CREATE KEYSPACE IF NOT EXISTS chat_system_target
  WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};
  ```

---

## Kiến thức đạt được & Hướng phát triển

### Kiến thức đạt được
- Thiết kế cơ sở dữ liệu NoSQL tối ưu hóa cho truy vấn (Query-driven design).
- Quản lý vận hành Apache Cassandra và ScyllaDB.
- Phát triển và tối ưu pipeline ETL sử dụng PySpark.
- Sử dụng Docker trong môi trường Big Data cục bộ.

### Hướng phát triển tiếp theo
- Thiết lập cơ chế ghi nhận real-time ETL thông qua Apache Kafka.
- Lập lịch định kỳ tiến trình ETL thông qua Apache Airflow.
- Triển khai Spark Cluster thực tế.
- Giám sát trạng thái cụm node thông qua Grafana.
