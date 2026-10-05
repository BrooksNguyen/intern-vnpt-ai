"""
Streamlit Dashboard — Phase 5
Visualizes all research results of the internship project.
Run: streamlit run phase_5_dashboard/app.py
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCYLLA_HOST = os.getenv("SCYLLA_HOST", "127.0.0.1")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", 9043))

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
# Import NLP functions (Case 4.1 — ensure correct function name)
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
    page_title="VNPT AI — Internship Dashboard",
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
    st.markdown("### 📊 Internship Dashboard")
    st.markdown("**Intern:** Nguyen Phuc Bach")
    st.markdown("**Department:** VNPT-AI")
    st.divider()
    st.markdown("#### Tech Stack")
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
st.markdown('<div class="main-header">📊 VNPT AI — Chat System Analytics Dashboard</div>', unsafe_allow_html=True)
st.caption("Action Plan & Research Results — Internship Project on ETL Pipeline & DB Optimization")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab_etl, tab3, tab4 = st.tabs([
    "🗄️ Database Overview & Hot Partition",
    "🧠 NLP Analytics",
    "⚡ ETL & Data Pipeline",
    "💬 Chat Room Explorer",
    "📝 Lessons Learned",
])

# =========================================================================
# TAB 1 — Database Overview
# =========================================================================
with tab1:
    st.header("Database Overview & Hot Partition Discovery")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Messages", "~20,000", help="Mock data from generate_mock_data.py")
    with col2:
        st.metric("Chat Rooms", "21", help="20 normal rooms + 1 hot room")
    with col3:
        st.metric("Hot Partition", "room_999", help="Accounts for ~80% of data")
    with col4:
        st.metric("Schema Strategy", "Time-Bucketing", help="Composite PK: (room_id, bucket_id)")

    st.divider()

    # Schema comparison
    st.subheader("Schema Before / After Comparison")
    col_before, col_after = st.columns(2)

    with col_before:
        st.markdown("#### ❌ Old Schema (Cassandra)")
        st.code("""CREATE TABLE chat_table (
    room_id text,
    message_id timeuuid,
    ...
    PRIMARY KEY (room_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

-- Problem: room_999 takes 80% → Hot Partition""", language="sql")

    with col_after:
        # Case 4.3 — Correct Primary Key description
        st.markdown("#### ✅ New Schema (ScyllaDB)")
        st.code("""CREATE TABLE chat_table_bucketed (
    room_id text,
    bucket_id text,
    message_id timeuuid,
    ...
    PRIMARY KEY ((room_id, bucket_id), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC)
AND default_time_to_live = 15552000
AND gc_grace_seconds = 864000;

-- message_id (timeuuid) already contains timestamp""", language="sql")

    st.markdown("""
On target database **ScyllaDB**:
- **Optimized Primary Key:** `PRIMARY KEY ((room_id, bucket_id), message_id)`
""")

    st.divider()

    # Charts
    st.subheader("Data Distribution Charts")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        room_dist_path = PROFILING_DIR / "room_distribution.png"
        if room_dist_path.exists():
            st.image(str(room_dist_path), caption="Message Distribution by Room", use_container_width=True)
        else:
            st.info("📁 File room_distribution.png not found")

    with chart_col2:
        bucket_path = ETL_IMAGES_DIR / "bucket_distribution.png"
        if bucket_path.exists():
            st.image(str(bucket_path), caption="Message Distribution by Bucket", use_container_width=True)
        else:
            st.info("📁 File bucket_distribution.png not found")


# =========================================================================
# TAB 2 — NLP Analytics
# =========================================================================
with tab2:
    st.header("🧠 Natural Language Processing (NLP)")

    # WordCloud
    st.subheader("WordCloud (room_999)")
    wc_path = NLP_IMAGES_DIR / "wordcloud_room_999.png"
    if wc_path.exists():
        st.image(str(wc_path), caption="Vietnamese WordCloud — room_999", use_container_width=True)
    else:
        st.warning("⚠️ WordCloud missing. Run `python phase_4_nlp_analysis/nlp_analytics_pipeline.py` to generate.")

    st.divider()

    # Sentiment Trend
    st.subheader("Sentiment Trend Over Time")
    sentiment_path = NLP_IMAGES_DIR / "sentiment_trend.png"
    if sentiment_path.exists():
        st.image(str(sentiment_path), caption="Daily sentiment trend chart", use_container_width=True)
    else:
        st.warning("⚠️ Sentiment chart missing. Run `python phase_4_nlp_analysis/nlp_analytics_pipeline.py` to generate.")

    st.divider()

    # Top Keywords
    st.subheader("Top 50 Keywords")
    keywords_path = NLP_DIR / "top_50_keywords.json"
    if keywords_path.exists():
        with open(keywords_path, "r", encoding="utf-8") as f:
            keywords = json.load(f)
        if keywords:
            df_kw = pd.DataFrame(keywords)
            col_chart, col_table = st.columns([2, 1])
            with col_chart:
                st.bar_chart(df_kw.set_index("keyword").head(20))
            with col_table:
                st.dataframe(df_kw, use_container_width=True, height=400)
    else:
        st.info("📁 File top_50_keywords.json not found")

    st.divider()

    # NLP Playground
    st.subheader("🎮 Interactive NLP Playground")
    user_input = st.text_area(
        "Enter Vietnamese message to analyze:",
        value="Mạng VNPT dạo này lag quá, fix giúp mình... =(((",
        height=100,
    )

    if st.button("Analyze ✨"):
        if clean_text and analyze_sentiment:
            # clean_text() returns tuple (str, list[str])
            cleaned_str, tokens = clean_text(user_input)
            # analyze_sentiment() takes list[str], returns (label, score)
            sentiment, score = analyze_sentiment(tokens)

            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.markdown("**Cleaned Text:**")
                st.code(cleaned_str)
            with res_col2:
                st.markdown("**Tokens:**")
                st.write(tokens)
            with res_col3:
                emoji_map = {"positive": "😊", "negative": "😞", "neutral": "😐"}
                color_map = {"positive": "green", "negative": "red", "neutral": "gray"}
                st.markdown("**Sentiment Result:**")
                st.markdown(
                    f"### {emoji_map.get(sentiment, '❓')} "
                    f":{color_map.get(sentiment, 'gray')}[{sentiment.upper()}]"
                )
                st.metric("Score", f"{score:.3f}")
        else:
            st.error("❌ NLP module not loaded. Check `nlp_analytics_pipeline.py`.")


# =========================================================================
# TAB ETL — Data Pipeline Visualization
# =========================================================================
with tab_etl:
    st.header("⚡ ETL Pipeline & Data Distribution")
    st.caption("Visualizations post-migration from Cassandra → ScyllaDB via PySpark")

    # ETL Architecture diagram
    st.subheader("ETL Pipeline Architecture")
    etl_arch_path = ETL_IMAGES_DIR / "etl_architecture.png"
    if etl_arch_path.exists():
        st.image(str(etl_arch_path), caption="ETL Pipeline Architecture Diagram", use_container_width=True)
    else:
        st.info("📁 File etl_architecture.png not found")

    st.divider()

    # Docker infrastructure
    docker_infra_path = ETL_IMAGES_DIR / "docker_infrastructure.png"
    if docker_infra_path.exists():
        st.subheader("Docker Compose Infrastructure")
        st.image(str(docker_infra_path), caption="Docker Infrastructure Architecture", use_container_width=True)
        st.divider()

    # Schema comparison
    schema_cmp_path = ETL_IMAGES_DIR / "schema_comparison.png"
    if schema_cmp_path.exists():
        st.subheader("Schema Comparison: Cassandra vs ScyllaDB")
        st.image(str(schema_cmp_path), caption="Primary Key Structure Comparison", use_container_width=True)
        st.divider()

    # Data distribution charts (2 columns)
    st.subheader("Post-Migration Data Distribution")
    etl_col1, etl_col2 = st.columns(2)

    with etl_col1:
        time_dist_path = ETL_IMAGES_DIR / "time_distribution.png"
        if time_dist_path.exists():
            st.image(str(time_dist_path), caption="Message Distribution by Time", use_container_width=True)

        device_dist_path = ETL_IMAGES_DIR / "device_distribution.png"
        if device_dist_path.exists():
            st.image(str(device_dist_path), caption="Message Distribution by Device", use_container_width=True)

        edited_path = ETL_IMAGES_DIR / "edited_ratio.png"
        if edited_path.exists():
            st.image(str(edited_path), caption="Edited Message Ratio", use_container_width=True)

    with etl_col2:
        msg_type_path = ETL_IMAGES_DIR / "msg_type_distribution.png"
        if msg_type_path.exists():
            st.image(str(msg_type_path), caption="Message Type Distribution", use_container_width=True)

        top_users_path = ETL_IMAGES_DIR / "top_users.png"
        if top_users_path.exists():
            st.image(str(top_users_path), caption="Top Active Users", use_container_width=True)

        spark_opt_path = ETL_IMAGES_DIR / "spark_optimization.png"
        if spark_opt_path.exists():
            st.image(str(spark_opt_path), caption="Spark I/O Optimization Results", use_container_width=True)

    st.divider()

    # Spark config summary
    st.subheader("Optimized Spark Configuration")
    spark_config = pd.DataFrame([
        {"Parameter": "spark.cassandra.output.batch.size.rows", "Value": "500", "Note": "Optimal batch write"},
        {"Parameter": "spark.cassandra.output.concurrent.writes", "Value": "4", "Note": "Concurrent writes"},
        {"Parameter": "spark.cassandra.input.split.size_in_mb", "Value": "64", "Note": "Read split size"},
        {"Parameter": "spark.sql.shuffle.partitions", "Value": "8", "Note": "Shuffle partitions"},
    ])
    st.dataframe(spark_config, use_container_width=True, hide_index=True)


# =========================================================================
# TAB 3 — Chat Room Explorer
# =========================================================================
with tab3:
    st.header("💬 Chat Room Explorer")
    st.caption("Message browser using Backtracking Pagination")

    if ChatBackendService is not None:
        # Connection controls
        with st.expander("⚙️ Connection Settings", expanded=False):
            db_host = st.text_input("ScyllaDB Host", value=SCYLLA_HOST)
            db_port = st.number_input("ScyllaDB Port", value=int(SCYLLA_PORT), min_value=1)

        room_id = st.text_input("🔍 Enter Room ID", value="room_999")
        msg_limit = st.slider("Max Messages", min_value=10, max_value=200, value=50, step=10)

        if st.button("🔎 Load Messages"):
            try:
                service = ChatBackendService(host=db_host, port=db_port)
                service.connect()
                messages = service.get_messages(room_id, limit=msg_limit)
                service.close()

                if messages:
                    st.success(f"✅ Loaded {len(messages)} messages from **{room_id}**")

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
                    st.warning(f"No messages found in **{room_id}**")

            except Exception as e:
                st.error(f"❌ Connection error: {e}")
                st.info("💡 Make sure ScyllaDB is running and has data in `chat_system_target`.")
    else:
        st.error("❌ Module `backend_service` not found.")


# =========================================================================
# TAB 4 — Lessons Learned
# =========================================================================
with tab4:
    st.header("📝 Lessons Learned — 11 Key Takeaways")

    lessons = [
        {
            "title": "1. TTL must align with Cold Archiver",
            "icon": "⏰",
            "desc": "TTL = 180 days (15,552,000s) ensuring data exists long enough for the 6-month Cold Archiver cycle.",
        },
        {
            "title": "2. Always set gc_grace_seconds",
            "icon": "🪦",
            "desc": "gc_grace_seconds = 864000 (10 days) to allow tombstones time to sync across replicas.",
        },
        {
            "title": "3. Filter on Partition Key",
            "icon": "🔍",
            "desc": "Filter by `bucket_id` (Partition Key) instead of `timestamp` to trigger Partition Pruning, avoiding Full Cluster Scans.",
        },
        {
            "title": "4. Data Reconciliation is mandatory",
            "icon": "✅",
            "desc": "After every ETL migration, count and verify Source vs Target: `assert src_count == tgt_count`.",
        },
        {
            "title": "5. Avoid hardcoding paths",
            "icon": "📁",
            "desc": "Use `pathlib.Path(__file__).resolve().parent` instead of `/home/jovyan/work/...`.",
        },
        {
            "title": "6. Check function names before import",
            "icon": "📦",
            "desc": "Always verify actual function names in modules: e.g., `clean_text` not `clean_text_vietnamese`.",
        },
        {
            "title": "7. Mind function return types",
            "icon": "🔄",
            "desc": "`clean_text()` returns `tuple[str, list[str]]`, not just a simple `str`.",
        },
        {
            "title": "8. Document schema must match code",
            "icon": "📋",
            "desc": "The `schema.cql` file must be 100% in sync with `scylla_ddl_manager.py` — including TTL and gc_grace_seconds.",
        },
        {
            "title": "9. Comment Docker paths",
            "icon": "🐳",
            "desc": "Paths like `/home/jovyan/work/` are only valid inside containers. Add warning comments.",
        },
        {
            "title": "10. Backtracking Pagination",
            "icon": "📖",
            "desc": "When fetching cross-bucket messages, use a month-decrement loop with a `max_backtrack_months` limit.",
        },
        {
            "title": "11. timeuuid contains timestamp",
            "icon": "🕐",
            "desc": "No need for `timestamp` in the clustering key because `message_id` (timeuuid) already embeds time information.",
        },
    ]

    for lesson in lessons:
        with st.expander(f"{lesson['icon']} {lesson['title']}", expanded=False):
            st.write(lesson["desc"])

    st.divider()
    st.success("🎓 Completed all 11 lessons → Project successfully evaluated with Excellence!")
