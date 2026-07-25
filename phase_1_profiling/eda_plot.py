import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count

CASS_HOST = os.getenv("CASSANDRA_HOST", "cassandra-source")
CASS_PORT = os.getenv("CASSANDRA_PORT", "9042")

logging.info("Starting Spark for EDA plotting...")
try:
    spark = SparkSession.builder \
        .appName("EDA_Plotting") \
        .config("spark.cassandra.connection.host", CASS_HOST) \
        .config("spark.cassandra.connection.port", CASS_PORT) \
        .getOrCreate()

    df = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="chat_table", keyspace="chat_system") \
        .load()

    logging.info("Grouping messages by room...")
    room_counts = df.groupBy("room_id") \
        .agg(count("message_id").alias("message_count")) \
        .orderBy(col("message_count").desc()) \
        .limit(10) \
        .toPandas()

    logging.info("Plotting chart...")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.bar(room_counts["room_id"], room_counts["message_count"], color='salmon')
    plt.title("Distribution of Messages by Room (Top 10)")
    plt.xlabel("Room ID")
    plt.ylabel("Number of Messages")
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    output_path = "/home/jovyan/work/phase_1_profiling/room_distribution.png"
    plt.savefig(output_path)
    logging.info(f"Chart saved successfully at {output_path}")

    spark.stop()
    sys.exit(0)
except Exception as e:
    logging.error(f"Plotting failed: {e}")
    sys.exit(1)
