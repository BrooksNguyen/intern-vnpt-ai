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
        "Dạ, em cảm ơn.", "Shop cho mình hỏi size giày này còn không?", "Lỗi mạng rồi bạn ơi", 
        "Ok chốt nhé.", "Mạng VNPT dạo này lag quá, fix giúp mình.", "Gói cước này nạp tiền ntn vậy?",
        "Ủa sao k gửi được ảnh nhỉ", "Tí nữa gọi lại nha", "Có ai hỗ trợ mình với =(((",
        "Alo alo 123", "Cho e hỏi chi phí lắp đặt wifi bao nhiêu ạ?", "Tuyệt vời", "Sp dùng chán quá",
        "Đã thanh toán xong.", "Check inbox đi bạn", "Mình đang bận xíu", "Để mình suy nghĩ thêm."
    ]

    msg_types = ["text", "image", "file", "link"]
    devices = ["ios", "android", "web", "desktop"]
    users = [f"user_{i}" for i in range(1, 100)]
    now = datetime.now()

    def get_random_ts():
        days = random.randint(0, 150)
        hour_weights = [1, 1, 0, 0, 0, 1, 3, 5, 8, 8, 7, 6, 6, 5, 5, 6, 7, 8, 9, 10, 10, 8, 5, 2]
        hours = random.choices(range(24), weights=hour_weights)[0]
        minutes = random.randint(0, 59)
        return now - timedelta(days=days, hours=hours, minutes=minutes)

    def get_random_device():
        return random.choices(devices, weights=[0.6, 0.3, 0.05, 0.05])[0]

    logging.info(f"Generating synthetic mock data (Approx. {MSG_LIMIT} records)...")

    insert_query = session.prepare("""
        INSERT INTO chat_table (room_id, message_id, user_id, content, msg_type, device, is_edited, timestamp)
        VALUES (?, now(), ?, ?, ?, ?, ?, ?)
    """)

    from cassandra.concurrent import execute_concurrent_with_args

    # Generate data for normal rooms
    normal_parameters = []
    for i in range(1, 21):
        room = f"room_{i}"
        msgs_count = random.randint(50, 150)
        for _ in range(msgs_count):
            normal_parameters.append((
                room,
                random.choice(users),
                random.choice(sample_messages),
                random.choice(msg_types),
                get_random_device(),
                random.random() < 0.05,
                get_random_ts()
            ))

    logging.info(f"Executing concurrent inserts for normal rooms ({len(normal_parameters)} records)...")
    execute_concurrent_with_args(session, insert_query, normal_parameters, concurrency=100)

    hot_room = "room_999"
    hot_msgs = int(MSG_LIMIT * 0.8)
    logging.info(f"Preparing heavy load ({hot_msgs} messages) for {hot_room} to simulate hot partition...")
    
    hot_parameters = []
    for i in range(hot_msgs):
        hot_parameters.append((
            hot_room,
            random.choice(users),
            random.choice(sample_messages),
            random.choice(msg_types),
            get_random_device(),
            random.random() < 0.05,
            get_random_ts()
        ))

    logging.info(f"Executing concurrent inserts for hot room ({len(hot_parameters)} records)...")
    execute_concurrent_with_args(session, insert_query, hot_parameters, concurrency=100)

    logging.info("Mock data generation completed.")
    row = session.execute("SELECT COUNT(*) FROM chat_table;").one()
    logging.info(f"Total rows verified in database: {row[0]}")

except Exception as e:
    logging.error(f"An error occurred during data generation: {e}")
finally:
    if cluster:
        cluster.shutdown()
        logging.info("Cassandra connection safely terminated.")
