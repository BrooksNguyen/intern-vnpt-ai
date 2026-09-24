"""
Backend Service — Phase 5
Mô phỏng backend truy vấn tin nhắn với thuật toán
phân trang lùi bucket tháng (Cross-Bucket Backtracking Pagination).
"""
import os
import sys
import logging
from datetime import datetime

from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCYLLA_HOST = os.getenv("SCYLLA_HOST", "127.0.0.1")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", 9043))


class ChatBackendService:
    """Service lớp mô phỏng backend chat, truy vấn ScyllaDB."""

    def __init__(self, host: str = SCYLLA_HOST, port: int = SCYLLA_PORT):
        self.host = host
        self.port = port
        self.cluster = None
        self.session = None

    def connect(self):
        """Kết nối tới ScyllaDB cluster."""
        logging.info(f"Connecting to ScyllaDB at {self.host}:{self.port}...")
        try:
            self.cluster = Cluster([self.host], port=self.port)
            self.session = self.cluster.connect('chat_system_target')
            logging.info("Connected to ScyllaDB successfully.")
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            sys.exit(1)

    def close(self):
        """Đóng kết nối an toàn."""
        if self.cluster:
            self.cluster.shutdown()
            logging.info("Connection closed.")

    def query_bucket(self, room_id: str, bucket_id: str, limit: int = 50) -> list[dict]:
        """
        Truy vấn tin nhắn từ một bucket cụ thể.
        Args:
            room_id: ID phòng chat
            bucket_id: Bucket tháng (format 'YYYY-MM')
            limit: Số lượng tin nhắn tối đa
        Returns:
            list[dict]: Danh sách tin nhắn
        """
        query = """
            SELECT room_id, bucket_id, message_id, user_id, content,
                   msg_type, device, is_edited, timestamp
            FROM chat_table_bucketed
            WHERE room_id = %s AND bucket_id = %s
            LIMIT %s;
        """
        rows = self.session.execute(query, (room_id, bucket_id, limit))
        results = []
        for row in rows:
            results.append({
                "room_id": row.room_id,
                "bucket_id": row.bucket_id,
                "message_id": str(row.message_id),
                "user_id": row.user_id,
                "content": row.content,
                "msg_type": row.msg_type,
                "device": row.device,
                "is_edited": row.is_edited,
                "timestamp": row.timestamp,
            })
        return results

    def get_messages(self, room_id: str, limit: int = 50, max_backtrack_months: int = 6) -> list[dict]:
        """
        Lấy tin nhắn với thuật toán Backtracking Pagination.

        Nếu bucket tháng hiện tại không đủ tin nhắn, tự động lùi về
        các tháng trước cho đến khi đủ `limit` hoặc hết `max_backtrack_months`.

        Args:
            room_id: ID phòng chat
            limit: Số lượng tin nhắn cần lấy (default: 50)
            max_backtrack_months: Số tháng tối đa được lùi (chặn vòng lặp vô hạn)
        Returns:
            list[dict]: Danh sách tin nhắn (tối đa `limit` bản ghi, không trùng lặp)
        """
        results = []
        curr_year, curr_month = datetime.now().year, datetime.now().month
        backtrack = 0

        while len(results) < limit and backtrack < max_backtrack_months:
            bucket_id = f"{curr_year:04d}-{curr_month:02d}"
            needed = limit - len(results)

            logging.debug(f"Querying bucket {bucket_id} for {needed} messages...")
            msgs = self.query_bucket(room_id, bucket_id, limit=needed)
            results.extend(msgs)

            # Lùi về tháng trước nếu chưa đủ tin nhắn
            curr_month -= 1
            if curr_month == 0:
                curr_month = 12
                curr_year -= 1
            backtrack += 1

        logging.info(
            f"get_messages(room={room_id}, limit={limit}): "
            f"returned {len(results)} messages, backtracked {backtrack} months."
        )
        return results

    def get_available_rooms(self) -> list[str]:
        """Lấy danh sách các room_id có trong hệ thống."""
        rows = self.session.execute(
            "SELECT DISTINCT room_id FROM chat_table_bucketed;"
        )
        rooms = sorted(set(row.room_id for row in rows))
        return rooms

    def get_room_stats(self) -> list[dict]:
        """Lấy thống kê số lượng tin nhắn theo room."""
        rows = self.session.execute(
            "SELECT room_id, bucket_id FROM chat_table_bucketed;"
        )
        from collections import Counter
        room_counter = Counter()
        for row in rows:
            room_counter[row.room_id] += 1

        stats = [{"room_id": k, "message_count": v}
                 for k, v in room_counter.most_common()]
        return stats


# ---------------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------------
def main():
    service = ChatBackendService()
    service.connect()

    # Demo: lấy 50 tin mới nhất của room_999
    messages = service.get_messages("room_999", limit=50)
    print(f"\n{'='*60}")
    print(f"  Fetched {len(messages)} messages from room_999")
    print(f"{'='*60}")
    for msg in messages[:5]:
        ts = msg["timestamp"].strftime("%Y-%m-%d %H:%M") if msg["timestamp"] else "N/A"
        print(f"  [{ts}] {msg['user_id']}: {msg['content'][:60]}...")

    if len(messages) > 5:
        print(f"  ... and {len(messages) - 5} more messages")

    # Demo: danh sách rooms
    rooms = service.get_available_rooms()
    print(f"\nAvailable rooms ({len(rooms)}): {rooms[:10]}...")

    service.close()


if __name__ == "__main__":
    main()
