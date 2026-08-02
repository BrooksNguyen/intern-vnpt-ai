import os
import random
import time
from datetime import datetime, timedelta
from cassandra.cluster import Cluster

HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1") # mặc định chạy local
PORT = 9042
MSG_LIMIT = 20000

print(f"Connecting to Cassandra {HOST}:{PORT}...")

# Cứ connect thẳng, rớt mạng thì văng lỗi đỏ ra terminal luôn
cluster = Cluster([HOST], port=PORT)
session = cluster.connect()

print("Connected!")

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
        msg_type text,
        device text,
        is_edited boolean,
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

msg_types = ["text", "image", "file", "link"]
devices = ["ios", "android", "web", "desktop"]
users = [f"user_{i}" for i in range(1, 100)]
now = datetime.now()

def get_random_ts():
    days = random.randint(0, 150)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return now - timedelta(days=days, hours=hours, minutes=minutes)

print(f"Generating mock data (~{MSG_LIMIT} msgs)... chờ xíu nha")

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
print(f"Bơm {hot_msgs} tin nhắn rác vào {hot_room} để test quá tải...")
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
        print(f"Pushed {i+1}/{hot_msgs} msgs...")

print("Xong!")
row = session.execute("SELECT COUNT(*) FROM chat_table;").one()
print(f"Total rows: {row[0]}")

# cluster.shutdown() # Kệ, tự exit
