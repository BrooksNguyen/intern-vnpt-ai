import os
import sys
import time
import logging
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = os.getenv("SCYLLA_HOST", "scylla-target")
PORT = int(os.getenv("SCYLLA_PORT", 9042))
DEFAULT_TTL = int(os.getenv("DEFAULT_TTL", 15552000)) # Mặc định 180 ngày

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

logging.info("Connected successfully!")

# Khởi tạo Keyspace dùng cơ chế NetworkTopologyStrategy của ScyllaDB
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS chat_system_target
    WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};
""")
session.set_keyspace("chat_system_target")

# Định nghĩa bảng tối ưu hóa tránh Hot Partition bằng Time Bucketing
# Tích hợp TWCS và TTL mặc định cho toàn bảng
session.execute(f"""
    CREATE TABLE IF NOT EXISTS chat_table_bucketed (
        room_id text,
        bucket_id text,
        message_id timeuuid,
        user_id text,
        content text,
        msg_type text,
        device text,
        is_edited boolean,
        timestamp timestamp,
        PRIMARY KEY ((room_id, bucket_id), message_id)
    ) WITH CLUSTERING ORDER BY (message_id DESC)
    AND default_time_to_live = {DEFAULT_TTL}
    AND compaction = {{
        'class': 'TimeWindowCompactionStrategy',
        'compaction_window_unit': 'DAYS',
        'compaction_window_size': 1
    }};
""")
logging.info(f"Target schema set up. Default TTL configuration: {DEFAULT_TTL} seconds.")

cluster.shutdown()
sys.exit(0)
