# ScyllaDB Architecture Design Report

Summary of design decisions for the Cassandra to ScyllaDB database migration.

## 1. Token-Aware Routing
ScyllaDB and Cassandra distribute data based on the Murmur3 hash function of the partition key. Configuring `TokenAware` routing on the client driver sends queries directly to the node holding the data, bypassing the Coordinator Node, thereby reducing latency.

## 2. Problems with the Legacy Architecture
- **Old Schema:** `PRIMARY KEY (room_id, message_id)`. All data for a chat room is stored on a single partition.
- **Problem:** Large chat rooms (e.g., `room_999`) cause Hot Partition issues, overloading specific nodes. Queries on secondary fields (`msg_type`, `device`) require `ALLOW FILTERING`, leading to full scans and degraded performance.

## 3. Solution: Composite Partition Key & Time Bucketing
The primary key was redesigned with an additional `bucket_id` field (format `YYYY-MM`):

```sql
PRIMARY KEY ((room_id, bucket_id), message_id)
```

**Advantages:** Data from large chat rooms is automatically split by month into different partitions, ensuring even load distribution across the cluster.

## 4. Backend Query Patterns

**Fetch 50 most recent messages:**
```sql
SELECT * FROM chat_system_target.chat_table_bucketed
WHERE room_id = 'room_1' AND bucket_id = '2026-07'
LIMIT 50;
```

**Paginated history retrieval:**
```sql
SELECT * FROM chat_system_target.chat_table_bucketed
WHERE room_id = 'room_1' AND bucket_id = '2026-07'
  AND message_id < 6ff1b35a-8405-11f1-8e64-af4db1424c6c
LIMIT 50;
```
*(Clustering order `message_id DESC` ensures results always return newest messages first).*

## 5. Data Lifecycle Management
- **TimeWindowCompactionStrategy (TWCS):** Groups SSTables by time window (e.g., 1 day). Optimizes deletion of old data and reduces CPU load compared to cross-compaction.
- **Time-To-Live (TTL):** Set `default_time_to_live = 15552000` (180 days) to automatically expire old data. The Cold Archiver runs on a 6-month cycle, ensuring data is archived before TTL expiration.
- **Tombstones:** Expired TTL records are marked as tombstones and retained for `gc_grace_seconds` (default 10 days = 864000s) to complete replica synchronization before physical deletion.
