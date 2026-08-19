"""
Script sinh biểu đồ EDA từ dữ liệu thật trong ScyllaDB.
Kết nối trực tiếp database, query, rồi vẽ chart.
"""
import os
import sys
import logging
from collections import Counter, defaultdict
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCYLLA_HOST = os.getenv("SCYLLA_HOST", "127.0.0.1")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", 9043))
CASS_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASS_PORT = int(os.getenv("CASSANDRA_PORT", 9042))

OUTPUT_DIR = "phase_3_pyspark_etl/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("phase_1_profiling", exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- Connect to Cassandra (source) ---
logging.info(f"Connecting to Cassandra source at {CASS_HOST}:{CASS_PORT}...")
try:
    cass_cluster = Cluster([CASS_HOST], port=CASS_PORT)
    cass_session = cass_cluster.connect('chat_system')
    logging.info("Connected to Cassandra source.")
except Exception as e:
    logging.error(f"Cannot connect to Cassandra: {e}")
    cass_cluster = None
    cass_session = None

# --- Connect to ScyllaDB (target) ---
logging.info(f"Connecting to ScyllaDB target at {SCYLLA_HOST}:{SCYLLA_PORT}...")
try:
    scylla_cluster = Cluster([SCYLLA_HOST], port=SCYLLA_PORT)
    scylla_session = scylla_cluster.connect('chat_system_target')
    logging.info("Connected to ScyllaDB target.")
except Exception as e:
    logging.error(f"Cannot connect to ScyllaDB: {e}")
    sys.exit(1)

# --- Query all data from ScyllaDB ---
logging.info("Querying all rows from chat_table_bucketed...")
rows = list(scylla_session.execute("SELECT room_id, bucket_id, user_id, content, msg_type, device, timestamp FROM chat_table_bucketed;"))
logging.info(f"Total rows fetched: {len(rows)}")

# --- 1. Room distribution ---
room_counter = Counter(r.room_id for r in rows)
top_rooms = room_counter.most_common(10)
rooms, counts = zip(*top_rooms)

fig, ax = plt.subplots(figsize=(10, 6))
colors = ['#e74c3c' if c == max(counts) else '#3498db' for c in counts]
bars = ax.bar(rooms, counts, color=colors, edgecolor='white')
ax.set_title('Top 10 Room theo so luong tin nhan', fontsize=14, fontweight='bold')
ax.set_xlabel('Room ID')
ax.set_ylabel('So luong tin nhan')
ax.set_yscale('log')
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1, f'{count:,}', ha='center', fontsize=9)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig('phase_1_profiling/room_distribution.png', dpi=150)
logging.info("Saved: phase_1_profiling/room_distribution.png")
plt.close()

# --- 2. Device distribution ---
device_counter = Counter(r.device for r in rows)
labels = list(device_counter.keys())
sizes = list(device_counter.values())
total = sum(sizes)
pct_labels = [f"{l} ({s/total*100:.1f}%)" for l, s in zip(labels, sizes)]
colors_pie = ['#3498db', '#2ecc71', '#e67e22', '#9b59b6']

fig, ax = plt.subplots(figsize=(8, 6))
ax.pie(sizes, labels=pct_labels, colors=colors_pie[:len(labels)], startangle=90, autopct='%1.1f%%')
ax.set_title('Phan phoi thiet bi', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/device_distribution.png', dpi=150)
logging.info(f"Saved: {OUTPUT_DIR}/device_distribution.png")
plt.close()

# --- 3. Time distribution (messages per hour) ---
hour_counter = Counter()
for r in rows:
    if r.timestamp:
        hour_counter[r.timestamp.hour] += 1

hours = list(range(24))
hour_counts = [hour_counter.get(h, 0) for h in hours]

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(hours, hour_counts, color='#3498db', edgecolor='white')
ax.set_title('Phan phoi tin nhan theo gio', fontsize=14, fontweight='bold')
ax.set_xlabel('Gio trong ngay')
ax.set_ylabel('So luong tin nhan')
ax.set_xticks(hours)
ax.set_xticklabels([f'{h}h' for h in hours])
plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/time_distribution.png', dpi=150)
logging.info(f"Saved: {OUTPUT_DIR}/time_distribution.png")
plt.close()

# --- 4. Message type distribution ---
type_counter = Counter(r.msg_type for r in rows)
types = list(type_counter.keys())
type_counts = list(type_counter.values())
type_colors = ['#2ecc71', '#e67e22', '#9b59b6', '#1abc9c']

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(types, type_counts, color=type_colors[:len(types)], edgecolor='white')
ax.set_title('Phan phoi loai tin nhan (msg_type)', fontsize=14, fontweight='bold')
ax.set_xlabel('Loai tin nhan')
ax.set_ylabel('So luong')
for i, (t, c) in enumerate(zip(types, type_counts)):
    ax.text(i, c + max(type_counts)*0.01, f'{c:,}', ha='center', fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/msg_type_distribution.png', dpi=150)
logging.info(f"Saved: {OUTPUT_DIR}/msg_type_distribution.png")
plt.close()

# --- 5. Bucket distribution for room_999 (hot partition demo) ---
bucket_counter = Counter()
for r in rows:
    if r.room_id == 'room_999':
        bucket_counter[r.bucket_id] += 1

if bucket_counter:
    buckets_sorted = sorted(bucket_counter.items())
    bucket_labels, bucket_counts = zip(*buckets_sorted)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(bucket_labels, bucket_counts, color='#2ecc71', edgecolor='white')
    ax.set_title('room_999: phan phoi tin nhan theo bucket_id (time-bucketing)', fontsize=13, fontweight='bold')
    ax.set_xlabel('bucket_id (yyyy-MM)')
    ax.set_ylabel('So luong tin nhan')
    for i, (b, c) in enumerate(zip(bucket_labels, bucket_counts)):
        ax.text(i, c + max(bucket_counts)*0.01, f'{c:,}', ha='center', fontsize=9)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/bucket_distribution.png', dpi=150)
    logging.info(f"Saved: {OUTPUT_DIR}/bucket_distribution.png")
    plt.close()

# --- 6. Spark optimization comparison (hardcoded config values, not data) ---
fig, ax = plt.subplots(figsize=(8, 5))
import numpy as np

params = ['batch.size.bytes', 'concurrent.writes', 'keepAliveMS']
default_vals = [512, 5, 600]
optimized_vals = [65536, 10, 10000]

x = np.arange(len(params))
width = 0.35

bars1 = ax.bar(x - width/2, default_vals, width, label='Default', color='#95a5a6', edgecolor='white')
bars2 = ax.bar(x + width/2, optimized_vals, width, label='Optimized', color='#2ecc71', edgecolor='white')

ax.set_title('So sanh cau hinh Spark: Default vs Optimized', fontsize=13, fontweight='bold')
ax.set_ylabel('Gia tri')
ax.set_xticks(x)
ax.set_xticklabels(params, fontsize=10)
ax.set_yscale('log')
ax.legend()

for bar, val in zip(bars1, default_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3, f'{val:,}', ha='center', fontsize=9, color='#7f8c8d')
for bar, val in zip(bars2, optimized_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3, f'{val:,}', ha='center', fontsize=9, color='#27ae60')

plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/spark_optimization.png', dpi=150)
logging.info(f"Saved: {OUTPUT_DIR}/spark_optimization.png")
plt.close()

# --- 7. User activity heatmap (top 15 users) ---
user_counter = Counter(r.user_id for r in rows)
top_users = user_counter.most_common(15)
u_names, u_counts = zip(*top_users)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(u_names[::-1], u_counts[::-1], color='#e67e22', edgecolor='white')
ax.set_title('Top 15 user hoat dong nhieu nhat', fontsize=13, fontweight='bold')
ax.set_xlabel('So luong tin nhan')
for i, c in enumerate(u_counts[::-1]):
    ax.text(c + max(u_counts)*0.01, i, f'{c:,}', va='center', fontsize=9)
plt.grid(axis='x', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/top_users.png', dpi=150)
logging.info(f"Saved: {OUTPUT_DIR}/top_users.png")
plt.close()

# --- 8. is_edited ratio ---
if cass_session:
    logging.info("Querying Cassandra source for is_edited stats...")
    cass_rows = list(cass_session.execute("SELECT is_edited FROM chat_table;"))
    edited = sum(1 for r in cass_rows if r.is_edited)
    not_edited = len(cass_rows) - edited

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie([not_edited, edited], labels=[f'Chua chinh sua ({not_edited:,})', f'Da chinh sua ({edited:,})'],
           colors=['#3498db', '#e74c3c'], autopct='%1.1f%%', startangle=90)
    ax.set_title('Ti le tin nhan da chinh sua (is_edited)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/edited_ratio.png', dpi=150)
    logging.info(f"Saved: {OUTPUT_DIR}/edited_ratio.png")
    plt.close()

# --- Print summary ---
print(f"\nTONG KET DU LIEU THUC:")
print(f"  Tong so ban ghi: {len(rows):,}")
print(f"  So room: {len(room_counter)}")
print(f"  Room lon nhat: {top_rooms[0][0]} ({top_rooms[0][1]:,} msgs)")
print(f"  Thiet bi: {dict(device_counter)}")
print(f"  Loai tin nhan: {dict(type_counter)}")
print(f"  Buckets room_999: {len(bucket_counter)}")
print(f"  Top 5 user: {top_users[:5]}")

# --- Cleanup ---
if cass_cluster:
    cass_cluster.shutdown()
scylla_cluster.shutdown()
logging.info("Done. All charts generated from real database data.")
