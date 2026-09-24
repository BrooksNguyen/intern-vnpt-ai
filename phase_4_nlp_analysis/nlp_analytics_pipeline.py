"""
NLP Analytics Pipeline — Phase 4
Đọc dữ liệu từ ScyllaDB, tiền xử lý văn bản tiếng Việt,
trích xuất Top 50 Keywords, sinh WordCloud và phân tích cảm xúc.

Hỗ trợ chế độ --offline để chạy không cần ScyllaDB (dùng mock data).
"""
import os
import sys
import re
import json
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

from underthesea import word_tokenize

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCYLLA_HOST = os.getenv("SCYLLA_HOST", "127.0.0.1")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", 9043))

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Stopwords
# ---------------------------------------------------------------------------
def load_stopwords(filepath="stopwords.txt"):
    try:
        full_path = BASE_DIR / filepath
        with open(full_path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except Exception as e:
        logging.error(f"Failed to load stopwords: {e}")
        sys.exit(1)

ALL_STOPWORDS = load_stopwords()

# ---------------------------------------------------------------------------
# Regex (pre-compiled for performance)
# ---------------------------------------------------------------------------
EMOTICONS_PATTERN = re.compile(r'(=[)(]+|:\)|:\(|<3|\?{2,}|!{2,})')
URL_PATTERN = re.compile(r'http[s]?://\S+|www\.\S+')
PUNCT_PATTERN = re.compile(r'[^\w\s]', flags=re.UNICODE)
SPACES_PATTERN = re.compile(r'\s+')

# ---------------------------------------------------------------------------
# Sentiment dictionaries
# ---------------------------------------------------------------------------
POSITIVE_WORDS = {
    "tuyệt_vời", "tốt", "xuất_sắc", "nhanh", "ổn", "thích", "hay",
    "cảm_ơn", "tuyệt", "ok", "chốt", "hài_lòng", "yêu", "đỉnh",
    "tốt_lắm", "chất_lượng", "ủng_hộ", "hỗ_trợ", "nhiệt_tình",
}
NEGATIVE_WORDS = {
    "lag", "lỗi", "chán", "tệ", "chậm", "hỏng", "kém", "mắc",
    "đắt", "dở", "tồi", "khó_chịu", "phàn_nàn", "bực", "thất_vọng",
    "sập", "die", "lừa_đảo", "trục_trặc",
}
POSITIVE_EMOTICONS = {"<3", "=))", "=)))", ":)"}
NEGATIVE_EMOTICONS = {"=((", "=(((", ":("}


# ---------------------------------------------------------------------------
# Core NLP functions
# ---------------------------------------------------------------------------
def clean_text(text: str) -> tuple[str, list[str]]:
    """
    Tiền xử lý văn bản tiếng Việt.
    Returns:
        tuple[str, list[str]]: (cleaned_string, list_of_tokens)
    """
    if not text:
        return "", []

    text = text.lower()
    text = URL_PATTERN.sub('', text)

    emoticons_found = EMOTICONS_PATTERN.findall(text)
    for i, emo in enumerate(emoticons_found):
        text = text.replace(emo, f" EMO_{i} ", 1)

    text = PUNCT_PATTERN.sub('', text)
    text = SPACES_PATTERN.sub(' ', text).strip()

    tokens = word_tokenize(text, format="list")

    cleaned_tokens = []
    for t in tokens:
        if t.startswith("EMO_"):
            cleaned_tokens.append(t)
        elif t.lower() not in ALL_STOPWORDS and len(t) > 1:
            cleaned_tokens.append(t)

    final_text = " ".join(cleaned_tokens)

    # Khôi phục emoticons gốc
    for i, emo in enumerate(emoticons_found):
        final_text = final_text.replace(f"EMO_{i}", emo)
        for j, token in enumerate(cleaned_tokens):
            if token == f"EMO_{i}":
                cleaned_tokens[j] = emo

    return final_text, cleaned_tokens


def analyze_sentiment(tokens: list[str]) -> tuple[str, float]:
    """
    Phân tích cảm xúc dựa trên từ điển + emoticons.
    Returns:
        tuple[str, float]: (label, score)
            label: 'positive' | 'negative' | 'neutral'
            score: [-1.0, 1.0]
    """
    pos_count = 0
    neg_count = 0

    for token in tokens:
        t_lower = token.lower().replace(" ", "_")
        if t_lower in POSITIVE_WORDS or token in POSITIVE_EMOTICONS:
            pos_count += 1
        elif t_lower in NEGATIVE_WORDS or token in NEGATIVE_EMOTICONS:
            neg_count += 1

    total = pos_count + neg_count
    if total == 0:
        return "neutral", 0.0

    score = (pos_count - neg_count) / total
    if score > 0.1:
        return "positive", round(score, 3)
    elif score < -0.1:
        return "negative", round(score, 3)
    else:
        return "neutral", round(score, 3)


# ---------------------------------------------------------------------------
# Data source functions
# ---------------------------------------------------------------------------
def fetch_all_messages_db(session):
    """Đọc toàn bộ tin nhắn từ ScyllaDB."""
    logging.info("Fetching all messages from ScyllaDB...")
    rows = session.execute(
        "SELECT room_id, user_id, content, timestamp FROM chat_table_bucketed;"
    )
    messages = []
    for row in rows:
        messages.append({
            "room_id": row.room_id,
            "user_id": row.user_id,
            "content": row.content or "",
            "timestamp": row.timestamp,
        })
    logging.info(f"Fetched {len(messages):,} messages.")
    return messages


def generate_mock_messages(count: int = 20000) -> list[dict]:
    """
    Sinh dữ liệu mock offline (giống generate_mock_data.py).
    Dùng khi không có kết nối ScyllaDB.
    """
    logging.info(f"Generating {count:,} mock messages for offline NLP analysis...")

    sample_messages = [
        "Dạ, em cảm ơn.", "Shop cho mình hỏi size giày này còn không?",
        "Lỗi mạng rồi bạn ơi", "Ok chốt nhé.",
        "Mạng VNPT dạo này lag quá, fix giúp mình.",
        "Gói cước này nạp tiền ntn vậy?",
        "Ủa sao k gửi được ảnh nhỉ", "Tí nữa gọi lại nha",
        "Có ai hỗ trợ mình với =(((",
        "Alo alo 123",
        "Cho e hỏi chi phí lắp đặt wifi bao nhiêu ạ?",
        "Tuyệt vời", "Sp dùng chán quá",
        "Đã thanh toán xong.", "Check inbox đi bạn",
        "Mình đang bận xíu", "Để mình suy nghĩ thêm.",
        "Wifi nhà mình lag quá trời luôn á =(((",
        "Dịch vụ tốt lắm, cảm ơn VNPT <3",
        "Tốc độ nhanh, ổn định, tuyệt vời! =)))",
        "Sao mạng chập chờn hoài vậy, chán ghê",
        "Nhân viên hỗ trợ nhiệt tình quá, cảm ơn bạn!",
        "Mạng bị sập rồi, lỗi liên tục!",
        "Gói cước mới chất lượng lắm, ủng hộ tiếp",
        "Thanh toán xong mà vẫn chưa được kích hoạt?? !!",
        "Đỉnh thật sự, dùng mấy tháng rồi không có vấn đề gì",
        "Kém quá, tốc độ chậm, hỗ trợ cũng tệ",
        "Em muốn đăng ký gói cước 200Mbps ạ",
        "Mạng trục trặc suốt tuần rồi bạn ơi =((",
        "Ok bạn, mình hài lòng với dịch vụ nhé :)",
        "Lắp đặt nhanh, thợ đến đúng hẹn, xuất sắc!",
        "Giá hơi mắc so với FPT nhưng ổn định hơn",
        "Bao giờ nâng cấp đường truyền vậy shop?",
        "Mình thất vọng quá, hứa mà không giữ lời",
        "Yêu VNPT <3 <3 dùng 5 năm rồi chưa có vấn đề",
    ]

    users = [f"user_{i}" for i in range(1, 100)]
    rooms = [f"room_{i}" for i in range(1, 21)] + ["room_999"] * 16
    now = datetime.now()

    messages = []
    for _ in range(count):
        days = random.randint(0, 150)
        hour_weights = [1, 1, 0, 0, 0, 1, 3, 5, 8, 8, 7, 6, 6, 5, 5, 6, 7, 8, 9, 10, 10, 8, 5, 2]
        hours = random.choices(range(24), weights=hour_weights)[0]
        minutes = random.randint(0, 59)
        ts = now - timedelta(days=days, hours=hours, minutes=minutes)

        messages.append({
            "room_id": random.choice(rooms),
            "user_id": random.choice(users),
            "content": random.choice(sample_messages),
            "timestamp": ts,
        })

    logging.info(f"Generated {len(messages):,} mock messages.")
    return messages


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------
def extract_top_keywords(all_tokens: list[str], top_n: int = 50) -> list[dict]:
    """Đếm tần suất và trả về Top N keywords."""
    counter = Counter(all_tokens)
    # Loại bỏ emoticons và token quá ngắn khỏi keyword list
    filtered = {k: v for k, v in counter.items()
                if len(k) > 1 and not re.match(r'^(EMO_\d+|[=:<()\[\]]+)$', k)}
    top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"keyword": kw, "count": cnt} for kw, cnt in top]


def generate_wordcloud(all_tokens: list[str], output_filename: str = "wordcloud_room_999.png"):
    """Sinh WordCloud tiếng Việt và lưu file PNG."""
    from wordcloud import WordCloud
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    text = " ".join(all_tokens)
    if not text.strip():
        logging.warning("No tokens for WordCloud — skipping.")
        return

    wc = WordCloud(
        width=1200, height=600,
        background_color='white',
        colormap='viridis',
        max_words=100,
        collocations=False,
    ).generate(text)

    plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout()

    out_path = IMAGES_DIR / output_filename
    plt.savefig(str(out_path), dpi=200)
    plt.close()
    logging.info(f"WordCloud saved to: {out_path}")


def generate_sentiment_trend(messages: list[dict], output_filename: str = "sentiment_trend.png"):
    """Vẽ biểu đồ xu hướng cảm xúc theo ngày."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    daily: dict[str, Counter] = {}
    for msg in messages:
        if msg["timestamp"] is None:
            continue
        day_str = msg["timestamp"].strftime("%Y-%m-%d")

        if day_str not in daily:
            daily[day_str] = Counter()
        daily[day_str][msg.get("sentiment", "neutral")] += 1

    if not daily:
        logging.warning("No data for sentiment trend.")
        return

    sorted_days = sorted(daily.keys())
    pos_pcts, neg_pcts, neu_pcts = [], [], []

    for day in sorted_days:
        total = sum(daily[day].values())
        pos_pcts.append(daily[day].get("positive", 0) / total * 100)
        neg_pcts.append(daily[day].get("negative", 0) / total * 100)
        neu_pcts.append(daily[day].get("neutral", 0) / total * 100)

    plt.figure(figsize=(14, 6))
    plt.plot(sorted_days, pos_pcts, label="Tích cực", color="#10b981", linewidth=2)
    plt.plot(sorted_days, neg_pcts, label="Tiêu cực", color="#ef4444", linewidth=2)
    plt.plot(sorted_days, neu_pcts, label="Trung tính", color="#6366f1", linewidth=2, linestyle="--")

    plt.xlabel("Ngày")
    plt.ylabel("Tỷ lệ (%)")
    plt.title("Xu hướng cảm xúc tin nhắn theo ngày")
    plt.legend()
    step = max(1, len(sorted_days) // 15)
    plt.xticks(
        range(0, len(sorted_days), step),
        [sorted_days[i] for i in range(0, len(sorted_days), step)],
        rotation=45,
    )
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()

    out_path = IMAGES_DIR / output_filename
    plt.savefig(str(out_path), dpi=200)
    plt.close()
    logging.info(f"Sentiment trend chart saved to: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="NLP Analytics Pipeline — Phase 4")
    parser.add_argument("--offline", action="store_true",
                        help="Chạy offline với mock data (không cần ScyllaDB)")
    parser.add_argument("--count", type=int, default=20000,
                        help="Số lượng mock messages khi chạy offline (default: 20000)")
    args = parser.parse_args()

    cluster = None

    if args.offline:
        logging.info("Running in OFFLINE mode with mock data...")
        messages = generate_mock_messages(count=args.count)
    else:
        logging.info(f"Connecting to ScyllaDB at {SCYLLA_HOST}:{SCYLLA_PORT}...")
        try:
            from cassandra.cluster import Cluster
            cluster = Cluster([SCYLLA_HOST], port=SCYLLA_PORT)
            session = cluster.connect('chat_system_target')
            messages = fetch_all_messages_db(session)
        except Exception as e:
            logging.warning(f"Database connection failed: {e}")
            logging.info("Falling back to OFFLINE mode with mock data...")
            messages = generate_mock_messages(count=args.count)

    # 1. Clean text & collect tokens
    logging.info("Step 1/5: Cleaning text and tokenizing...")
    all_tokens = []
    for msg in messages:
        cleaned_str, tokens = clean_text(msg["content"])
        msg["cleaned"] = cleaned_str
        msg["tokens"] = tokens
        all_tokens.extend(tokens)

    logging.info(f"Total tokens collected: {len(all_tokens):,}")

    # 2. Top 50 Keywords
    logging.info("Step 2/5: Extracting Top 50 Keywords...")
    top_keywords = extract_top_keywords(all_tokens, top_n=50)
    keywords_path = BASE_DIR / "top_50_keywords.json"
    with open(keywords_path, "w", encoding="utf-8") as f:
        json.dump(top_keywords, f, ensure_ascii=False, indent=2)
    logging.info(f"Top 50 keywords saved to: {keywords_path}")

    # Print top 10 for quick review
    logging.info("Top 10 Keywords:")
    for kw in top_keywords[:10]:
        logging.info(f"  {kw['keyword']:>20}: {kw['count']:>5,}")

    # 3. WordCloud
    logging.info("Step 3/5: Generating WordCloud...")
    generate_wordcloud(all_tokens)

    # 4. Sentiment Analysis
    logging.info("Step 4/5: Analyzing sentiment for all messages...")
    for msg in messages:
        label, score = analyze_sentiment(msg["tokens"])
        msg["sentiment"] = label
        msg["sentiment_score"] = score

    # 5. Sentiment Trend Chart
    logging.info("Step 5/5: Generating sentiment trend chart...")
    generate_sentiment_trend(messages)

    # Summary
    sentiments = Counter(m["sentiment"] for m in messages)
    total = len(messages)
    logging.info("=" * 50)
    logging.info("  NLP ANALYTICS PIPELINE — KẾT QUẢ TỔNG HỢP")
    logging.info("=" * 50)
    logging.info(f"  Tổng tin nhắn phân tích : {total:>8,}")
    logging.info(f"  Tổng tokens trích xuất  : {len(all_tokens):>8,}")
    for label in ["positive", "negative", "neutral"]:
        cnt = sentiments.get(label, 0)
        pct = cnt / total * 100 if total else 0
        logging.info(f"  {label:>10}: {cnt:>6,} ({pct:.1f}%)")
    logging.info("=" * 50)

    # Output files summary
    logging.info("Output files:")
    logging.info(f"  ✅ {keywords_path}")
    logging.info(f"  ✅ {IMAGES_DIR / 'wordcloud_room_999.png'}")
    logging.info(f"  ✅ {IMAGES_DIR / 'sentiment_trend.png'}")

    if cluster:
        cluster.shutdown()
    logging.info("NLP Analytics Pipeline completed successfully.")


if __name__ == "__main__":
    main()

