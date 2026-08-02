import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the required package is available
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession

CASS_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASS_PORT = os.getenv("CASSANDRA_PORT", "9042")

def main():
    logging.info("Initializing SparkSession...")
    try:
        spark = SparkSession.builder \
            .appName("SparkCassandraTest") \
            .config("spark.cassandra.connection.host", CASS_HOST) \
            .config("spark.cassandra.connection.port", CASS_PORT) \
            .getOrCreate()

        logging.info("Spark initialized successfully.")
        
        logging.info(f"Attempting to read from Cassandra at {CASS_HOST}:{CASS_PORT}...")
        df = spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="chat_table", keyspace="chat_system") \
            .load()

        total = df.count()
        logging.info(f"Connection test passed. Total records in Cassandra: {total}")
        
        logging.info("Sample data:")
        df.select("room_id", "user_id", "content", "msg_type", "device", "is_edited", "timestamp").show(5, truncate=False)
        
    except Exception as e:
        logging.error(f"Spark connection test failed due to an error: {e}")
        sys.exit(1)
    finally:
        if 'spark' in locals():
            spark.stop()
            logging.info("SparkSession safely terminated.")

if __name__ == "__main__":
    main()
