import os
import sys
import time
import logging
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = os.getenv("SCYLLA_HOST", "scylla-target")
PORT = int(os.getenv("SCYLLA_PORT", 9042))

logging.info(f"Connecting to ScyllaDB {HOST}:{PORT}...")
retries = 10
cluster = None
session = None

for i in range(retries):
    try:
        cluster = Cluster([HOST], port=PORT)
        session = cluster.connect()
        break
    except Exception as e:
        logging.warning(f"Retry {i+1}/{retries} failed: {e}. Waiting 5s...")
        time.sleep(5)

if not session:
    logging.error("ScyllaDB connection failed.")
    sys.exit(1)

logging.info("Connected to ScyllaDB.")

session.execute("""
    CREATE KEYSPACE IF NOT EXISTS chat_system_target
    WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};
""")
session.set_keyspace("chat_system_target")

session.execute("""
    CREATE TABLE IF NOT EXISTS chat_table_bucketed (
        room_id text,
        bucket_id text,
        message_id timeuuid,
        user_id text,
        content text,
        timestamp timestamp,
        PRIMARY KEY ((room_id, bucket_id), message_id)
    ) WITH CLUSTERING ORDER BY (message_id DESC);
""")
logging.info("Created target schema in ScyllaDB.")

cluster.shutdown()
sys.exit(0)
