import os
import sys
import re
import logging
from underthesea import word_tokenize
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCYLLA_HOST = os.getenv("SCYLLA_HOST", "127.0.0.1")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", 9043))

# Vietnamese stopwords (common function words with no semantic value)
VIETNAMESE_STOPWORDS = {
    "bị", "bởi", "cả", "các", "cái", "cần", "càng", "chỉ", "chiếc", "cho",
    "chứ", "chưa", "chuyện", "có", "có_thể", "cứ", "của", "cùng", "cũng",
    "đã", "đang", "đây", "để", "đến", "đều", "điều", "do", "đó", "được",
    "dù", "dưới", "gì", "hay", "hoặc", "hơn", "là", "lại", "lên", "lúc",
    "mà", "mỗi", "một", "này", "nên", "nếu", "ngay", "nhiều", "như", "nhưng",
    "những", "nơi", "nữa", "phải", "qua", "ra", "rằng", "rất", "rồi",
    "sau", "sẽ", "so", "sự", "tại", "theo", "thì", "trên", "trước",
    "từ", "và", "vẫn", "về", "vì", "với", "vừa",
}

# Basic English stopwords (for mixed-language messages)
ENGLISH_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "it", "its", "this", "that", "not", "or", "and", "but", "if", "so",
}

ALL_STOPWORDS = VIETNAMESE_STOPWORDS | ENGLISH_STOPWORDS


def clean_text(text):
    """5-step text preprocessing pipeline: lowercase, remove URLs,
    remove special chars, tokenize (underthesea), remove stopwords."""
    if not text:
        return ""

    # Step 1: Lowercase
    text = text.lower()

    # Step 2: Remove URLs
    text = re.sub(r'http[s]?://\S+|www\.\S+', '', text)

    # Step 3: Remove special characters and punctuation (keep Vietnamese unicode chars)
    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()

    # Step 4: Tokenize using underthesea (Vietnamese word segmentation)
    tokens = word_tokenize(text, format="list")

    # Step 5: Remove stopwords
    cleaned_tokens = [t for t in tokens if t.lower() not in ALL_STOPWORDS and len(t) > 1]

    return " ".join(cleaned_tokens)


def main():
    logging.info(f"Connecting to ScyllaDB at {SCYLLA_HOST}:{SCYLLA_PORT}...")
    cluster = None

    try:
        cluster = Cluster([SCYLLA_HOST], port=SCYLLA_PORT)
        session = cluster.connect('chat_system_target')
        logging.info("Connected to keyspace: chat_system_target")

        # Fetch 5 sample messages for preprocessing demo (DoD requirement)
        logging.info("Fetching 5 sample messages for preprocessing demo...")
        rows = session.execute(
            "SELECT room_id, user_id, content FROM chat_table_bucketed LIMIT 5;"
        )

        print("\n" + "=" * 70)
        print("  TEXT PREPROCESSING RESULTS")
        print("=" * 70)

        for idx, row in enumerate(rows, 1):
            original = row.content
            cleaned = clean_text(original)
            print(f"\n  Message #{idx} [{row.room_id} | {row.user_id}]")
            print(f"  Original : {original}")
            print(f"  Cleaned  : {cleaned}")

        print("\n" + "=" * 70)

        # Edge-case demo (hardcoded, no DB required)
        print("\n  EDGE-CASE DEMO")
        print("  " + "-" * 60)
        edge_cases = [
            "Mạng VNPT dạo này lag quá, fix giúp mình... https://vnpt.com.vn/ho-tro",
            "Cho e hỏi chi phí lắp đặt wifi bao nhiêu ạ??? =)))",
            "OK chốt nhé!!! Tuyệt vời luôn á <3 <3",
            "Alo alo 123... có ai hỗ trợ mình với =((((",
            "Check inbox đi bạn, mình đã thanh toán xong rồi nha.",
        ]
        for idx, text in enumerate(edge_cases, 1):
            cleaned = clean_text(text)
            print(f"\n  Edge-case #{idx}")
            print(f"  Original : {text}")
            print(f"  Cleaned  : {cleaned}")

        print("\n" + "=" * 70)
        logging.info("Text preprocessing demo completed.")

    except Exception as e:
        logging.error(f"Error: {e}")

        # Fallback: run demo without DB connection
        logging.info("Running fallback demo with hardcoded sample messages...")
        print("\n" + "=" * 70)
        print("  TEXT PREPROCESSING RESULTS (FALLBACK - NO DB)")
        print("=" * 70)

        fallback_messages = [
            "Dạ, em cảm ơn.",
            "Shop cho mình hỏi size giày này còn không?",
            "Mạng VNPT dạo này lag quá, fix giúp mình.",
            "Cho e hỏi chi phí lắp đặt wifi bao nhiêu ạ?",
            "Có ai hỗ trợ mình với =(((",
        ]
        for idx, text in enumerate(fallback_messages, 1):
            cleaned = clean_text(text)
            print(f"\n  Message #{idx}")
            print(f"  Original : {text}")
            print(f"  Cleaned  : {cleaned}")

        print("\n" + "=" * 70)

    finally:
        if cluster:
            cluster.shutdown()
            logging.info("Connection closed.")


if __name__ == "__main__":
    main()
