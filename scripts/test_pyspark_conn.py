import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession

CASS_HOST = os.getenv("CASSANDRA_HOST", "cassandra-source")
CASS_PORT = os.getenv("CASSANDRA_PORT", "9042")

logging.info("Starting SparkSession...")
try:
    spark = SparkSession.builder \
        .appName("SparkCassandraTest") \
        .config("spark.cassandra.connection.host", CASS_HOST) \
        .config("spark.cassandra.connection.port", CASS_PORT) \
        .getOrCreate()

    logging.info("Spark initialized successfully.")
    
    df = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="chat_table", keyspace="chat_system") \
        .load()

    total = df.count()
    logging.info(f"Connection test passed. Records in Cassandra: {total}")
    
    df.select("room_id", "user_id", "content", "timestamp").show(5, truncate=False)
    
    spark.stop()
    sys.exit(0)
except Exception as e:
    logging.error(f"Spark connection test failed: {e}")
    sys.exit(1)
