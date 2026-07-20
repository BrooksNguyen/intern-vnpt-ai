# PHASE 0: HƯỚNG DẪN CÀI ĐẶT MÔI TRƯỜNG VÀ DOCKER

Để làm được dự án này, em cần cài đặt **Docker** và **Docker Compose**. Việc sử dụng Docker giúp em có ngay lập tức cụm cơ sở dữ liệu (Cassandra, ScyllaDB) và môi trường Spark mà không cần cài cắm phức tạp trực tiếp vào hệ điều hành.

## 1. Hướng dẫn cài đặt Docker Desktop
*Khuyên dùng máy tính có ít nhất 8GB RAM (tốt nhất là 16GB) vì chạy cùng lúc nhiều Big Data engines khá tốn tài nguyên.*

**Đối với Windows / Mac:**
1. Truy cập trang chủ Docker: [Tải Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Tải bản cài đặt tương thích với máy của em (Intel chip hay Apple Silicon đối với Mac) rồi chạy file setup.
3. **Lưu ý cho Windows:** Trong quá trình cài đặt, nhớ tick chọn vào ô **"Use WSL 2 instead of Hyper-V"** (Windows Subsystem for Linux 2) để Docker chạy nhẹ và đỡ tốn pin hơn.
4. Sau khi cài xong, mở ứng dụng Docker Desktop lên và chờ cho đến khi icon Docker ở góc màn hình chuyển sang màu xanh lá cây (Engine running).
5. **Kiểm tra cài đặt:** Mở Terminal (Mac) hoặc Command Prompt/PowerShell (Windows), gõ lệnh:
   ```bash
   docker --version
   docker-compose --version
   ```
   *(Nếu in ra được phiên bản tức là máy đã cài đặt thành công).*

## 2. Cách sử dụng file `docker-compose.yml`
File `docker-compose.yml` đã được cấu hình sẵn cho 3 hệ thống:
*   `cassandra_source`: Cơ sở dữ liệu nguồn, chạy ở port 9042.
*   `scylla_target`: Cơ sở dữ liệu đích, chạy ở port 9043 (bên ngoài).
*   `pyspark_workspace`: Môi trường lập trình Jupyter Notebook, chạy ở port 8888.

**Các lệnh Docker Compose cơ bản:**

1. **Khởi động toàn bộ hệ thống:**
   Mở Terminal, di chuyển (`cd`) vào thư mục chứa file `docker-compose.yml` và chạy:
   ```bash
   docker compose up -d
   ```
   *(Lần đầu chạy sẽ hơi lâu vì Docker cần tải các image nặng về máy).*

2. **Kiểm tra trạng thái hệ thống:**
   ```bash
   docker ps
   ```
   *Lệnh này dùng để check xem các container có chạy bình thường hay không. Em phải thấy đủ cả 3 container báo trạng thái `Up`.*

3. **Tắt hệ thống (khi hết giờ làm việc):**
   ```bash
   docker compose down
   ```
   *Lệnh này sẽ tắt và dọn dẹp các container, dữ liệu trong database và code của em vẫn được giữ lại trên ổ đĩa nhờ cơ chế Volume.*

## 3. Truy cập vào môi trường PySpark (Jupyter Notebook)
Môi trường code Python và Spark đã được chuẩn bị sẵn trong container `pyspark_workspace`.
1. Để lấy link đăng nhập, gõ lệnh xem log của container:
   ```bash
   docker logs pyspark_workspace
   ```
2. Tìm trong log dòng có chứa URL bắt đầu bằng `http://127.0.0.1:8888/?token=...`
3. Copy link đó dán vào trình duyệt Web để bắt đầu code.
4. Mọi file `.ipynb` em tạo trong thư mục `work/` trên giao diện web sẽ tự động đồng bộ ra thư mục `notebooks` ở máy tính thật của em.

## 4. Cách khởi tạo PySpark Session kết nối với Cassandra
Trong Jupyter Notebook, tạo một file Python mới. Để Spark kết nối được với Cassandra, em cần tải gói kết nối `spark-cassandra-connector`.

**Code mẫu chạy thử:**
```python
import os
# Thiết lập gói kết nối khi khởi động Spark (Tương thích Spark 3.x)
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("ChatDataMigration") \
    .config("spark.cassandra.connection.host", "cassandra-source") \
    .config("spark.cassandra.connection.port", "9042") \
    .getOrCreate()

print("Spark Session đã sẵn sàng!")
```

## 5. Vào CQL Shell thao tác trực tiếp với Database
Nếu em muốn gõ lệnh SQL (CQL) trực tiếp để xem bảng dữ liệu:
*   **Vào Cassandra:**
    ```bash
    docker exec -it cassandra_source cqlsh
    ```
*   **Vào ScyllaDB:**
    ```bash
    docker exec -it scylla_target cqlsh
    ```
