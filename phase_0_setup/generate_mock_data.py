import os
import sys
import random
import time
import logging
from datetime import datetime, timedelta
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
PORT = int(os.getenv("CASSANDRA_PORT", 9042))
MSG_LIMIT = int(os.getenv("MSG_LIMIT", 20000))

logging.info(f"Initializing connection to Cassandra {HOST}:{PORT}...")
retries = 10
cluster = None
session = None

for i in range(retries):
    try:
        cluster = Cluster([HOST], port=PORT)
        session = cluster.connect()
        logging.info("Connection established successfully.")
        break
    except Exception as e:
        logging.warning(f"Connection retry {i+1}/{retries} failed: {e}. Waiting 10 seconds before retrying...")
        time.sleep(10)

if not session:
    logging.error("Failed to connect to Cassandra after multiple retries. Exiting.")
    sys.exit(1)

try:
    logging.info("Configuring Keyspace 'chat_system'...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS chat_system
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """)
    session.set_keyspace("chat_system")

    logging.info("Configuring Table 'chat_table'...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS chat_table (
            room_id text,
            message_id timeuuid,
            user_id text,
            content text,
            msg_type text,
            device text,
            is_edited boolean,
            timestamp timestamp,
            PRIMARY KEY (room_id, message_id)
        ) WITH CLUSTERING ORDER BY (message_id DESC);
    """)

    sample_messages = [
        "System initialization complete.", "Health check ping.", "Message received.", "Status code 200.", 
        "Data synchronization in progress.", "Review requested for PR #1042.", "Deployment successful.", 
        "Task completed.", "Running diagnostic tests.", "Connection verified.", "Error detected in module A.", 
        "Executing batch operations.", "Logs flushed.", "Connection terminated."
    ]

    msg_types = ["text", "image", "file", "link"]
    devices = ["ios", "android", "web", "desktop"]
    users = [f"user_{i}" for i in range(1, 100)]
    now = datetime.now()

    def get_random_ts():
        days = random.randint(0, 150)
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        return now - timedelta(days=days, hours=hours, minutes=minutes)

    logging.info(f"Generating synthetic mock data (Approx. {MSG_LIMIT} records)...")

    insert_query = session.prepare("""
        INSERT INTO chat_table (room_id, message_id, user_id, content, msg_type, device, is_edited, timestamp)
        VALUES (?, now(), ?, ?, ?, ?, ?, ?)
    """)

    for i in range(1, 21):
        room = f"room_{i}"
        msgs_count = random.randint(50, 150)
        for _ in range(msgs_count):
            session.execute(insert_query, [
                room,
                random.choice(users),
                random.choice(sample_messages),
                random.choice(msg_types),
                random.choice(devices),
                random.random() < 0.05,
                get_random_ts()
            ])

    hot_room = "room_999"
    hot_msgs = int(MSG_LIMIT * 0.8)
    logging.info(f"Injecting heavy load ({hot_msgs} messages) into {hot_room} to simulate hot partition...")
    for i in range(hot_msgs):
        session.execute(insert_query, [
            hot_room,
            random.choice(users),
            random.choice(sample_messages),
            random.choice(msg_types),
            random.choice(devices),
            random.random() < 0.05,
            get_random_ts()
        ])
        if (i + 1) % 4000 == 0:
            logging.info(f"Progress: {i+1}/{hot_msgs} records pushed.")

    logging.info("Mock data generation completed.")
    row = session.execute("SELECT COUNT(*) FROM chat_table;").one()
    logging.info(f"Total rows verified in database: {row[0]}")

except Exception as e:
    logging.error(f"An error occurred during data generation: {e}")
finally:
    if cluster:
        cluster.shutdown()
        logging.info("Cassandra connection safely terminated.")
