import os
import time

# phải set cái này để spark tự kéo thư viện cassandra về, không là lỗi ClassNotFound
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_format

# hardcode IP cho lẹ để test local, lúc lên prod thì tính sau
CASS_HOST = "cassandra-source" 
SCYLLA_HOST = "scylla-target"

print("Khởi động Spark session...")
spark = SparkSession.builder \
    .appName("ETL_Cassandra_to_Scylla") \
    .config("spark.cassandra.connection.host", CASS_HOST) \
    .config("spark.cassandra.connection.port", "9042") \
    .getOrCreate()

print("Bắt đầu đọc data từ Cassandra")
start_time = time.time()

df_chat = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="chat_table", keyspace="chat_system") \
    .load()

# df_chat.show(5) # debug xem data lên chưa

print(f"Đọc xong, tổng record: {df_chat.count()} dòng. Chờ xíu...")

# FIXME: tạm chia bucket theo tháng (yyyy-MM) để chống hot partition cho phòng chat đông.
# Cơ mà mấy cái nhóm ế chả ai chat cũng bị chia tháng thì hơi rác. Chắc để rảnh sửa lại sau.
df_new = df_chat.withColumn("bucket_id", date_format(col("timestamp"), "yyyy-MM"))

print(f"Đang đẩy sang ScyllaDB ở IP {SCYLLA_HOST}...")

# đoạn này dùng mode append vì sợ nó đè mất data cũ trên scylla
df_new.write \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="chat_table_bucketed", keyspace="chat_system_target") \
    .option("spark.cassandra.connection.host", SCYLLA_HOST) \
    .option("spark.cassandra.connection.port", "9042") \
    .mode("append") \
    .save()

print(f"Done! Tổng thời gian chạy: {time.time() - start_time} giây")

# spark.stop() # để comment ở đây nhỡ chạy trên notebook nó sập mất session
