-- ==========================================
-- Cấu hình Database Nguồn (Apache Cassandra)
-- ==========================================
CREATE KEYSPACE IF NOT EXISTS chat_system
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE chat_system;

-- Bảng lưu trữ tin nhắn gốc (room_id làm Partition Key đơn lẻ)
-- Nhược điểm: Dễ bị nghẽn Hot Partition nếu phòng chat có số lượng tin nhắn khổng lồ
CREATE TABLE IF NOT EXISTS chat_table (
    room_id text,
    message_id timeuuid,
    user_id text,
    content text,
    msg_type text,      -- text, image, file, link
    device text,        -- ios, android, web, desktop
    is_edited boolean,  -- trạng thái tin nhắn đã bị sửa hay chưa
    timestamp timestamp,
    PRIMARY KEY (room_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);


-- ==========================================
-- Cấu hình Database Đích (ScyllaDB)
-- ==========================================
CREATE KEYSPACE IF NOT EXISTS chat_system_target
WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};

USE chat_system_target;

-- Bảng tối ưu hóa (sử dụng Composite Partition Key: room_id + bucket_id)
-- Ưu điểm: Phân tán dữ liệu của room_id lớn theo phân mảnh thời gian tránh nghẽn
CREATE TABLE IF NOT EXISTS chat_table_bucketed (
    room_id text,
    bucket_id text,     -- YYYY-MM
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
