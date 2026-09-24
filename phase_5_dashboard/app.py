"""
Streamlit Dashboard — Phase 5
Giao diện trực quan hóa toàn bộ kết quả nghiên cứu đề tài thực tập.
Chạy: streamlit run phase_5_dashboard/app.py
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import streamlit as st

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
NLP_DIR = PROJECT_ROOT / "phase_4_nlp_analysis"
NLP_IMAGES_DIR = NLP_DIR / "images"
PROFILING_DIR = PROJECT_ROOT / "phase_1_profiling"
ETL_IMAGES_DIR = PROJECT_ROOT / "phase_3_pyspark_etl" / "images"

# ---------------------------------------------------------------------------
# Import NLP functions (Case 4.1 — đúng tên hàm)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(NLP_DIR))
try:
    from nlp_analytics_pipeline import clean_text, analyze_sentiment
except ImportError:
    clean_text = None
    analyze_sentiment = None

# ---------------------------------------------------------------------------
# Import Backend Service
# ---------------------------------------------------------------------------
sys.path.insert(0, str(BASE_DIR))
try:
    from backend_service import ChatBackendService
except ImportError:
    ChatBackendService = None

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="VNPT AI — Dashboard Thực Tập",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #005baa, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/VNPT_Logo.svg/1200px-VNPT_Logo.svg.png", width=150)
    st.markdown("### 📊 Dashboard Thực Tập")
    st.markdown("**Thực tập sinh:** Nguyễn Phúc Bách")
    st.markdown("**Đơn vị:** VNPT-AI")
    st.divider()
    st.markdown("#### Công nghệ sử dụng")
    st.markdown("""
    - 🗄️ Apache Cassandra → ScyllaDB
    - ⚡ Apache Spark (PySpark)
    - 🐍 Python / Underthesea NLP
    - 🐳 Docker Compose
    - 📊 Streamlit Dashboard
    """)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">📊 VNPT AI — Dashboard Phân Tích Hệ Thống Chat</div>', unsafe_allow_html=True)
st.caption("Kế hoạch hành động & kết quả nghiên cứu — Đề tài thực tập xây dựng Pipeline ETL và Tối ưu hóa CSDL")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🗄️ Tổng quan CSDL & Hot Partition",
    "🧠 Khai phá NLP",
    "💬 Chat Room Explorer",
    "📝 Sổ tay nghiệp vụ",
])

# =========================================================================
# TAB 1 — Tổng quan CSDL
# =========================================================================
with tab1:
    st.header("Tổng quan Cơ sở Dữ liệu & Phát hiện Hot Partition")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng tin nhắn", "~20,000", help="Dữ liệu mock từ generate_mock_data.py")
    with col2:
        st.metric("Số phòng chat", "21", help="20 phòng bình thường + 1 hot room")
    with col3:
        st.metric("Hot Partition", "room_999", help="Chiếm ~80% tổng dữ liệu")
    with col4:
        st.metric("Schema Strategy", "Time-Bucketing", help="Composite PK: (room_id, bucket_id)")

    st.divider()

    # Schema comparison
    st.subheader("So sánh Schema Before / After")
    col_before, col_after = st.columns(2)

    with col_before:
        st.markdown("#### ❌ Schema Cũ (Cassandra)")
        st.code("""CREATE TABLE chat_table (
    room_id text,
    message_id timeuuid,
    ...
    PRIMARY KEY (room_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

-- Vấn đề: room_999 chiếm 80% → Hot Partition""", language="sql")

    with col_after:
        # Case 4.3 — Mô tả Primary Key ĐÚNG (không có timestamp trong clustering key)
        st.markdown("#### ✅ Schema Mới (ScyllaDB)")
        st.code("""CREATE TABLE chat_table_bucketed (
    room_id text,
    bucket_id text,
    message_id timeuuid,
    ...
    PRIMARY KEY ((room_id, bucket_id), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC)
AND default_time_to_live = 15552000
AND gc_grace_seconds = 864000;

-- message_id (timeuuid) đã bao gồm thời gian""", language="sql")

    st.markdown("""
Trên cơ sở dữ liệu đích **ScyllaDB**:
- **Primary Key tối ưu:** `PRIMARY KEY ((room_id, bucket_id), message_id)`
""")
    # ✅ message_id (timeuuid) đã bao gồm thông tin thời gian bên trong
    # ✅ Không cần timestamp riêng trong clustering key

    st.divider()

    # Charts
    st.subheader("Biểu đồ phân phối dữ liệu")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        room_dist_path = PROFILING_DIR / "room_distribution.png"
        if room_dist_path.exists():
            st.image(str(room_dist_path), caption="Phân phối tin nhắn theo Room", use_container_width=True)
        else:
            st.info("📁 Chưa có file room_distribution.png")

    with chart_col2:
        bucket_path = ETL_IMAGES_DIR / "bucket_distribution.png"
        if bucket_path.exists():
            st.image(str(bucket_path), caption="Phân phối tin nhắn theo Bucket", use_container_width=True)
        else:
            st.info("📁 Chưa có file bucket_distribution.png")


# =========================================================================
# TAB 2 — NLP Analytics
# =========================================================================
with tab2:
    st.header("🧠 Khai phá Ngôn ngữ Tự nhiên (NLP)")

    # WordCloud
    st.subheader("Đám mây Từ vựng (WordCloud)")
    wc_path = NLP_IMAGES_DIR / "wordcloud_room_999.png"
    if wc_path.exists():
        st.image(str(wc_path), caption="WordCloud tiếng Việt — room_999", use_container_width=True)
    else:
        st.warning("⚠️ Chưa có ảnh WordCloud. Chạy `python phase_4_nlp_analysis/nlp_analytics_pipeline.py` để sinh.")

    st.divider()

    # Sentiment Trend
    st.subheader("Xu hướng Cảm xúc theo Thời gian")
    sentiment_path = NLP_IMAGES_DIR / "sentiment_trend.png"
    if sentiment_path.exists():
        st.image(str(sentiment_path), caption="Biểu đồ xu hướng cảm xúc theo ngày", use_container_width=True)
    else:
        st.warning("⚠️ Chưa có biểu đồ sentiment. Chạy `python phase_4_nlp_analysis/nlp_analytics_pipeline.py` để sinh.")

    st.divider()

    # Top Keywords
    st.subheader("Top 50 Keywords")
    keywords_path = NLP_DIR / "top_50_keywords.json"
    if keywords_path.exists():
        with open(keywords_path, "r", encoding="utf-8") as f:
            keywords = json.load(f)
        if keywords:
            import pandas as pd
            df_kw = pd.DataFrame(keywords)
            col_chart, col_table = st.columns([2, 1])
            with col_chart:
                st.bar_chart(df_kw.set_index("keyword").head(20))
            with col_table:
                st.dataframe(df_kw, use_container_width=True, height=400)
    else:
        st.info("📁 Chưa có file top_50_keywords.json")

    st.divider()

    # NLP Playground
    st.subheader("🎮 Interactive NLP Playground")
    user_input = st.text_area(
        "Nhập tin nhắn tiếng Việt để phân tích:",
        value="Mạng VNPT dạo này lag quá, fix giúp mình... =(((",
        height=100,
    )

    if st.button("Phân tích ngay ✨"):
        if clean_text and analyze_sentiment:
            # clean_text() trả về tuple (str, list[str])
            cleaned_str, tokens = clean_text(user_input)
            # analyze_sentiment() nhận list[str], trả (label, score)
            sentiment, score = analyze_sentiment(tokens)

            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.markdown("**Văn bản đã làm sạch:**")
                st.code(cleaned_str)
            with res_col2:
                st.markdown("**Tokens:**")
                st.write(tokens)
            with res_col3:
                emoji_map = {"positive": "😊", "negative": "😞", "neutral": "😐"}
                color_map = {"positive": "green", "negative": "red", "neutral": "gray"}
                st.markdown("**Kết quả Cảm xúc:**")
                st.markdown(
                    f"### {emoji_map.get(sentiment, '❓')} "
                    f":{color_map.get(sentiment, 'gray')}[{sentiment.upper()}]"
                )
                st.metric("Score", f"{score:.3f}")
        else:
            st.error("❌ Module NLP chưa được cài đặt. Kiểm tra file `nlp_analytics_pipeline.py`.")


# =========================================================================
# TAB 3 — Chat Room Explorer
# =========================================================================
with tab3:
    st.header("💬 Chat Room Explorer")
    st.caption("Trình duyệt tin nhắn với cơ chế Backtracking Pagination")

    if ChatBackendService is not None:
        # Connection controls
        with st.expander("⚙️ Cấu hình kết nối", expanded=False):
            db_host = st.text_input("ScyllaDB Host", value=SCYLLA_HOST)
            db_port = st.number_input("ScyllaDB Port", value=int(SCYLLA_PORT), min_value=1)

        room_id = st.text_input("🔍 Nhập Room ID", value="room_999")
        msg_limit = st.slider("Số tin nhắn tối đa", min_value=10, max_value=200, value=50, step=10)

        if st.button("🔎 Tải tin nhắn"):
            try:
                service = ChatBackendService(host=db_host, port=db_port)
                service.connect()
                messages = service.get_messages(room_id, limit=msg_limit)
                service.close()

                if messages:
                    st.success(f"✅ Đã tải {len(messages)} tin nhắn từ **{room_id}**")

                    for msg in messages:
                        ts = msg["timestamp"].strftime("%Y-%m-%d %H:%M") if msg["timestamp"] else "N/A"
                        device_emoji = {
                            "ios": "📱", "android": "🤖",
                            "web": "🌐", "desktop": "💻"
                        }.get(msg.get("device", ""), "❓")

                        with st.chat_message("user"):
                            st.markdown(
                                f"**{msg['user_id']}** {device_emoji} "
                                f"· `{msg['bucket_id']}` · {ts}"
                            )
                            st.write(msg["content"])
                else:
                    st.warning(f"Không tìm thấy tin nhắn nào trong **{room_id}**")

            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {e}")
                st.info("💡 Đảm bảo ScyllaDB đang chạy và có dữ liệu trong `chat_system_target`.")
    else:
        st.error("❌ Module `backend_service` chưa được tìm thấy.")


# =========================================================================
# TAB 4 — Sổ tay nghiệp vụ
# =========================================================================
with tab4:
    st.header("📝 Sổ Tay Nghiệp Vụ — 11 Bài Học Kinh Nghiệm")

    lessons = [
        {
            "title": "1. TTL phải khớp với Cold Archiver",
            "icon": "⏰",
            "desc": "TTL = 180 ngày (15,552,000s) để dữ liệu tồn tại đủ lâu cho Cold Archiver 6 tháng hoạt động.",
        },
        {
            "title": "2. Luôn thêm gc_grace_seconds",
            "icon": "🪦",
            "desc": "gc_grace_seconds = 864000 (10 ngày) để tombstone có đủ thời gian đồng bộ giữa các replica.",
        },
        {
            "title": "3. Filter trên Partition Key",
            "icon": "🔍",
            "desc": "Lọc theo `bucket_id` (Partition Key) thay vì `timestamp` để kích hoạt Partition Pruning, tránh Full Cluster Scan.",
        },
        {
            "title": "4. Data Reconciliation là bắt buộc",
            "icon": "✅",
            "desc": "Sau mỗi ETL migration, đếm và so khớp Source vs Target: `assert src_count == tgt_count`.",
        },
        {
            "title": "5. Không hardcode đường dẫn",
            "icon": "📁",
            "desc": "Dùng `pathlib.Path(__file__).resolve().parent` thay vì `/home/jovyan/work/...`.",
        },
        {
            "title": "6. Kiểm tra tên hàm trước khi import",
            "icon": "📦",
            "desc": "Luôn xác nhận tên hàm thực tế trong module: `clean_text` chứ không phải `clean_text_vietnamese`.",
        },
        {
            "title": "7. Chú ý return type của hàm",
            "icon": "🔄",
            "desc": "`clean_text()` trả về `tuple[str, list[str]]`, không phải `str` đơn thuần.",
        },
        {
            "title": "8. Schema tài liệu phải đồng bộ code",
            "icon": "📋",
            "desc": "File `schema.cql` phải khớp 100% với `scylla_ddl_manager.py` — cả TTL lẫn gc_grace_seconds.",
        },
        {
            "title": "9. Comment đường dẫn Docker",
            "icon": "🐳",
            "desc": "Đường dẫn `/home/jovyan/work/` chỉ hợp lệ bên trong container. Thêm comment cảnh báo.",
        },
        {
            "title": "10. Backtracking Pagination",
            "icon": "📖",
            "desc": "Khi lấy tin nhắn cross-bucket, dùng vòng lặp lùi tháng có giới hạn `max_backtrack_months`.",
        },
        {
            "title": "11. timeuuid đã chứa thông tin thời gian",
            "icon": "🕐",
            "desc": "Không cần `timestamp` trong clustering key vì `message_id` (timeuuid) đã tự bao gồm thời gian.",
        },
    ]

    for lesson in lessons:
        with st.expander(f"{lesson['icon']} {lesson['title']}", expanded=False):
            st.write(lesson["desc"])

    st.divider()
    st.success("🎓 Hoàn thành tất cả 11 bài học → Đề tài đạt tiêu chuẩn nghiệm thu Xuất sắc!")
