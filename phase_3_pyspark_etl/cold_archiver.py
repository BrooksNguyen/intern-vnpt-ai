import os
import sys
import time
import argparse
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ.setdefault('PYSPARK_SUBMIT_ARGS', '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell')

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, lit

def main():
    parser = argparse.ArgumentParser(description="PySpark Cold Archiver: ScyllaDB to Parquet")
    parser.add_argument("--months-old", type=int, default=6, help="Archive data older than this many months (default: 6)")
    parser.add_argument("--output-dir", type=str, default="data/cold_archive", help="Output directory for Parquet files")
    args = parser.parse_args()

    SCYLLA_HOST = os.getenv("SCYLLA_HOST", "scylla-target")
    SCYLLA_PORT = os.getenv("SCYLLA_PORT", "9042")

    logging.info(f"Initiating PySpark Cold Archiver (Archiving data older than {args.months_old} months)...")
    
    spark = SparkSession.builder \
        .appName("PySpark_Cold_Archiver") \
        .config("spark.cassandra.connection.host", SCYLLA_HOST) \
        .config("spark.cassandra.connection.port", SCYLLA_PORT) \
        .getOrCreate()
    
    try:
        logging.info(f"Connecting to ScyllaDB cluster at {SCYLLA_HOST}:{SCYLLA_PORT}...")
        start_time = time.time()
        
        df = spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="chat_table_bucketed", keyspace="chat_system_target") \
            .load()
            
        logging.info(f"Successfully connected and initialized read stream in {time.time() - start_time:.2f} seconds.")

        from dateutil.relativedelta import relativedelta
        current_date = datetime.now()
        cutoff_date = current_date - relativedelta(months=args.months_old)
        cutoff_bucket = cutoff_date.strftime("%Y-%m")
        
        logging.info(f"Filtering cold buckets older than: {cutoff_bucket}...")

        # Filter trên partition key 'bucket_id' để tối ưu Partition Pruning (Zero Full Scan)
        df_cold = df.filter(col("bucket_id") < lit(cutoff_bucket)) \
                    .withColumn("year", year(col("timestamp"))) \
                    .withColumn("month", month(col("timestamp")))
                    
        logging.info(f"Exporting data to Parquet format at {args.output_dir}...")
        
        df_cold.write \
            .mode("overwrite") \
            .partitionBy("year", "month") \
            .parquet(args.output_dir)
            
        logging.info(f"Successfully archived cold data to {args.output_dir} in {time.time() - start_time:.2f} seconds.")

    except Exception as e:
        logging.error(f"Cold Archiver failed with error: {e}")
        sys.exit(1)
    finally:
        spark.stop()
        logging.info("SparkSession safely terminated.")

if __name__ == "__main__":
    main()
