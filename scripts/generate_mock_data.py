import os
import sys
import random
import time
import logging
from datetime import datetime, timedelta
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = os.getenv("CASSANDRA_HOST", "cassandra-source")
PORT = int(os.getenv("CASSANDRA_PORT", 9042))

logging.info(f"Connecting to Cassandra {HOST}:{PORT}...")
retries = 10
cluster = None
session = None

for i in range(retries):
    try:
        cluster = Cluster([HOST], port=PORT)
        session = cluster.connect()
        break
    except Exception as e:
        logging.warning(f"Retry {i+1}/{retries} failed: {e}. Waiting 10s...")
        time.sleep(10)

if not session:
    logging.error("Cassandra connection failed.")
    sys.exit(1)

logging.info("Connected!")

session.execute("""
    CREATE KEYSPACE IF NOT EXISTS chat_system
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
""")
session.set_keyspace("chat_system")

session.execute("""
    CREATE TABLE IF NOT EXISTS chat_table (
        room_id text,
        message_id timeuuid,
        user_id text,
        content text,
        timestamp timestamp,
        PRIMARY KEY (room_id, message_id)
    ) WITH CLUSTERING ORDER BY (message_id DESC);
""")

sample_messages = [
    "test", "ping", "hello", "123", "check", 
    "bug rùi", "ai rảnh review code giùm", "ok", 
    "done", "test chat", "alo alo", "lỗi rồi", 
    "chạy thử thôi", "hahaha", "cáp treo lại đứt à"
]

users = [f"user_{i}" for i in range(1, 21)]
now = datetime.now()

def get_random_ts():
    days = random.randint(0, 150)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return now - timedelta(days=days, hours=hours, minutes=minutes)

logging.info("Generating mock data...")

insert_query = session.prepare("""
    INSERT INTO chat_table (room_id, message_id, user_id, content, timestamp)
    VALUES (?, now(), ?, ?, ?)
""")

for i in range(1, 11):
    room = f"room_{i}"
    msgs_count = random.randint(20, 50)
    for _ in range(msgs_count):
        session.execute(insert_query, [
            room,
            random.choice(users),
            random.choice(sample_messages),
            get_random_ts()
        ])

hot_room = "room_999"
hot_msgs = 2000
logging.info(f"Injecting {hot_msgs} messages into hot room {hot_room}...")
for i in range(hot_msgs):
    session.execute(insert_query, [
        hot_room,
        random.choice(users),
        random.choice(sample_messages),
        get_random_ts()
    ])
    if (i + 1) % 500 == 0:
        logging.info(f"Pushed {i+1}/{hot_msgs} msgs...")

logging.info("Mock data generated successfully.")
row = session.execute("SELECT COUNT(*) FROM chat_table;").one()
logging.info(f"Total rows: {row[0]}")

cluster.shutdown()
