import os
import sys
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ.setdefault('PYSPARK_SUBMIT_ARGS', '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell')

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_format

def main():
    parser = argparse.ArgumentParser(description="PySpark ETL Migration: Cassandra to ScyllaDB")
    parser.add_argument("--mode", type=str, default="optimized", choices=["default", "optimized"],
                        help="Execution mode: default or optimized")
    args = parser.parse_args()

    CASS_HOST = os.getenv("CASSANDRA_HOST", "cassandra-source")
    CASS_PORT = os.getenv("CASSANDRA_PORT", "9042")
    SCYLLA_HOST = os.getenv("SCYLLA_HOST", "scylla-target")
    SCYLLA_PORT = os.getenv("SCYLLA_PORT", "9042")

    logging.info(f"Initiating PySpark ETL Migration process (mode={args.mode})...")
    
    builder = SparkSession.builder \
        .appName(f"PySpark_ETL_Migration_{args.mode}") \
        .config("spark.cassandra.connection.host", CASS_HOST) \
        .config("spark.cassandra.connection.port", CASS_PORT)

    if args.mode == "optimized":
        logging.info("Applying advanced performance tuning (Batching & Concurrency)...")
        builder = builder \
            .config("spark.cassandra.output.batch.size.bytes", "65536") \
            .config("spark.cassandra.output.concurrent.writes", "10") \
            .config("spark.cassandra.connection.keepAliveMS", "10000")

    spark = builder.getOrCreate()
    
    try:
        logging.info(f"Connecting to source Cassandra cluster at {CASS_HOST}:{CASS_PORT}...")
        read_start = time.time()
        
        df_source = spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="chat_table", keyspace="chat_system") \
            .load()
            
        logging.info(f"Successfully connected and initialized read stream in {time.time() - read_start:.2f} seconds.")

        df_transformed = df_source.withColumn("bucket_id", date_format(col("timestamp"), "yyyy-MM"))

        logging.info(f"Initiating data load to target ScyllaDB cluster at {SCYLLA_HOST}:{SCYLLA_PORT}...")
        write_start = time.time()
        
        df_transformed.write \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="chat_table_bucketed", keyspace="chat_system_target") \
            .option("spark.cassandra.connection.host", SCYLLA_HOST) \
            .option("spark.cassandra.connection.port", SCYLLA_PORT) \
            .mode("append") \
            .save()
            
        write_time = time.time() - write_start
        logging.info(f"Data migration completed. Total write time: {write_time:.2f} seconds.")

    except Exception as e:
        logging.error(f"ETL Migration failed with error: {e}")
        sys.exit(1)
    finally:
        spark.stop()
        logging.info("SparkSession safely terminated.")

if __name__ == "__main__":
    main()
