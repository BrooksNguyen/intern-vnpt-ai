-- Cassandra (source)
CREATE KEYSPACE IF NOT EXISTS chat_system
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE chat_system;

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


-- ScyllaDB (target) - composite PK tránh hot partition
CREATE KEYSPACE IF NOT EXISTS chat_system_target
WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};

USE chat_system_target;

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
AND default_time_to_live = 2592000
AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
};
