"""
Backend Service — Phase 5
Simulates a chat backend service, querying ScyllaDB with
Cross-Bucket Backtracking Pagination algorithm.
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
    """Service class simulating chat backend, querying ScyllaDB."""

    def __init__(self, host: str = SCYLLA_HOST, port: int = SCYLLA_PORT):
        self.host = host
        self.port = port
        self.cluster = None
        self.session = None

    def connect(self):
        """Connect to ScyllaDB cluster."""
        logging.info(f"Connecting to ScyllaDB at {self.host}:{self.port}...")
        try:
            self.cluster = Cluster([self.host], port=self.port)
            self.session = self.cluster.connect('chat_system_target')
            logging.info("Connected to ScyllaDB successfully.")
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            sys.exit(1)

    def close(self):
        """Close connection safely."""
        if self.cluster:
            self.cluster.shutdown()
            logging.info("Connection closed.")

    def query_bucket(self, room_id: str, bucket_id: str, limit: int = 50) -> list[dict]:
        """
        Query messages from a specific bucket.
        Args:
            room_id: Chat room ID
            bucket_id: Month bucket (format 'YYYY-MM')
            limit: Maximum number of messages
        Returns:
            list[dict]: List of messages
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
        Retrieve messages using Backtracking Pagination algorithm.

        If the current month's bucket does not have enough messages, it automatically
        backtracks to previous months until it reaches the `limit` or `max_backtrack_months`.

        Args:
            room_id: Chat room ID
            limit: Number of messages needed (default: 50)
            max_backtrack_months: Maximum months to backtrack (prevent infinite loop)
        Returns:
            list[dict]: List of messages (up to `limit` records)
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

            # Backtrack to previous month if not enough messages
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
        """Get list of available room_ids in the system."""
        rows = self.session.execute(
            "SELECT DISTINCT room_id FROM chat_table_bucketed;"
        )
        rooms = sorted(set(row.room_id for row in rows))
        return rooms

    def get_room_stats(self) -> list[dict]:
        """Get statistics of message count per room."""
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

    # Demo: fetch 50 newest messages from room_999
    messages = service.get_messages("room_999", limit=50)
    print(f"\n{'='*60}")
    print(f"  Fetched {len(messages)} messages from room_999")
    print(f"{'='*60}")
    for msg in messages[:5]:
        ts = msg["timestamp"].strftime("%Y-%m-%d %H:%M") if msg["timestamp"] else "N/A"
        print(f"  [{ts}] {msg['user_id']}: {msg['content'][:60]}...")

    if len(messages) > 5:
        print(f"  ... and {len(messages) - 5} more messages")

    # Demo: list of rooms
    rooms = service.get_available_rooms()
    print(f"\nAvailable rooms ({len(rooms)}): {rooms[:10]}...")

    service.close()


if __name__ == "__main__":
    main()
