import os
import sys
import re
import logging
from underthesea import word_tokenize
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCYLLA_HOST = os.getenv("SCYLLA_HOST", "127.0.0.1")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", 9043))

def load_stopwords(filepath="stopwords.txt"):
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        full_path = os.path.join(dir_path, filepath)
        with open(full_path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except Exception as e:
        logging.error(f"Failed to load stopwords from {filepath}: {e}")
        sys.exit(1)

ALL_STOPWORDS = load_stopwords()

EMOTICONS_PATTERN = r'(=[)(]+|:\)|:\(|<3|\?{2,}|!{2,})'

def clean_text(text):
    if not text:
        return ""

    text = text.lower()
    
    text = re.sub(r'http[s]?://\S+|www\.\S+', '', text)

    emoticons_found = re.findall(EMOTICONS_PATTERN, text)
    for i, emo in enumerate(emoticons_found):
        text = text.replace(emo, f" EMO_{i} ", 1)

    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
    
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = word_tokenize(text, format="list")
    
    cleaned_tokens = []
    for t in tokens:
        if t.startswith("EMO_"):
            cleaned_tokens.append(t)
        elif t.lower() not in ALL_STOPWORDS and len(t) > 1:
            cleaned_tokens.append(t)
    
    final_text = " ".join(cleaned_tokens)

    for i, emo in enumerate(emoticons_found):
        final_text = final_text.replace(f"EMO_{i}", emo)
        
    return final_text

def main():
    logging.info(f"Connecting to ScyllaDB at {SCYLLA_HOST}:{SCYLLA_PORT}...")
    
    try:
        cluster = Cluster([SCYLLA_HOST], port=SCYLLA_PORT)
        session = cluster.connect('chat_system_target')
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        sys.exit(1)

    logging.info("Fetching sample messages...")
    rows = session.execute("SELECT room_id, user_id, content FROM chat_table_bucketed LIMIT 5;")

    for row in rows:
        cleaned = clean_text(row.content)
        print(f"[{row.room_id}|{row.user_id}] RAW: {row.content}")
        print(f"[{row.room_id}|{row.user_id}] CLN: {cleaned}\n")

    edge_cases = [
        "Mạng VNPT dạo này lag quá, fix giúp mình... https://vnpt.com.vn/ho-tro",
        "Cho e hỏi chi phí lắp đặt wifi bao nhiêu ạ??? =)))",
        "OK chốt nhé!!! Tuyệt vời luôn á <3 <3",
        "Alo alo 123... có ai hỗ trợ mình với =((((",
        "Check inbox đi bạn, mình đã thanh toán xong rồi nha.",
    ]
    
    print("--- Edge cases ---")
    for text in edge_cases:
        print(f"RAW: {text}")
        print(f"CLN: {clean_text(text)}\n")

    cluster.shutdown()

if __name__ == "__main__":
    main()
