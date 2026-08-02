import os

os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession

CASS_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASS_PORT = "9042"

print("Starting SparkSession...")
spark = SparkSession.builder \
    .appName("SparkCassandraTest") \
    .config("spark.cassandra.connection.host", CASS_HOST) \
    .config("spark.cassandra.connection.port", CASS_PORT) \
    .getOrCreate()

print("Spark initialized successfully.")

# Cứ đọc thẳng xem sao, nếu có biến thì báo lỗi terminal
df = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="chat_table", keyspace="chat_system") \
    .load()

total = df.count()
print(f"Connection test passed. Records in Cassandra: {total}")

df.select("room_id", "user_id", "content", "msg_type", "device", "is_edited", "timestamp").show(5, truncate=False)

# spark.stop()
