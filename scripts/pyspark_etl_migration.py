import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_format, coalesce, lit

CASS_HOST = os.getenv("CASSANDRA_HOST", "cassandra-source")
CASS_PORT = os.getenv("CASSANDRA_PORT", "9042")
SCYLLA_HOST = os.getenv("SCYLLA_HOST", "scylla-target")
SCYLLA_PORT = os.getenv("SCYLLA_PORT", "9042")

logging.info("Starting Spark ETL Migration...")
try:
    spark = SparkSession.builder \
        .appName("ETL_Cassandra_ScyllaDB") \
        .config("spark.cassandra.connection.host", CASS_HOST) \
        .config("spark.cassandra.connection.port", CASS_PORT) \
        .getOrCreate()

    raw_df = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="chat_table", keyspace="chat_system") \
        .load()

    total = raw_df.count()
    logging.info(f"Read {total} records from Cassandra.")

    # Fix hot partition issue by adding bucket_id
    clean_df = raw_df.withColumn(
        "bucket_id",
        coalesce(date_format(col("timestamp"), "yyyy-MM"), lit("unknown"))
    )

    clean_df.select("room_id", "bucket_id", "message_id", "user_id").show(5)

    logging.info("Writing to ScyllaDB...")
    clean_df.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="chat_table_bucketed", keyspace="chat_system_target") \
        .option("spark.cassandra.connection.host", SCYLLA_HOST) \
        .option("spark.cassandra.connection.port", SCYLLA_PORT) \
        .mode("append") \
        .save()

    logging.info(f"Migration completed! Moved {total} records.")
    spark.stop()
    sys.exit(0)

except Exception as e:
    logging.error(f"Migration failed: {e}")
    sys.exit(1)
