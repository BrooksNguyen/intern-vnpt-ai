# VNPT AI Internship — Chat System Data Optimization

## Overview

This project was developed during an internship at VNPT AI, with the goal of building, optimizing, and analyzing data for a large-scale chat messaging storage system. The core focus is migrating data (ETL) from Apache Cassandra to ScyllaDB to resolve the Hot Partition problem, setting up a Vietnamese NLP processing pipeline, and building an interactive reporting dashboard.

The project is divided into **6 Phases** corresponding to the internship roadmap.

---

## Project Roadmap (6 Phases)

- **Phase 0: Environment Setup**
  Deploy a local Big Data infrastructure using Docker Compose, including: Apache Cassandra (source), ScyllaDB (target), and PySpark. Generate synthetic mock data that exhibits the Hot Partition phenomenon for testing.

- **Phase 1: Data Profiling & EDA**
  Query and evaluate data on Cassandra. Discover that chat room `room_999` accounts for the majority of messages, leading to load imbalance (Hot Partition).

- **Phase 2: ScyllaDB Schema Design**
  Redesign the database schema on ScyllaDB. Transform the Partition Key from `room_id` to `(room_id, bucket_id)` for monthly time-bucketing, completely resolving the Hot Partition issue.

- **Phase 3: PySpark ETL Pipeline**
  Build an ETL pipeline to migrate data from Cassandra to ScyllaDB. Optimize Spark I/O configuration (batch size, concurrent writes) and implement a Cold Archiver to store old data in Parquet format.

- **Phase 4: NLP Analysis on Chat Messages**
  Vietnamese text preprocessing using the `underthesea` library (word segmentation, stopword removal, emoticon preservation). Sentiment analysis with a custom dictionary and WordCloud visualization to identify user interaction trends.

- **Phase 5: API & Dashboard**
  Build a data-serving API with FastAPI (supporting Backtracking Pagination) and a real-time reporting dashboard with Streamlit displaying NLP analytics, ETL charts, and a Chat Room Explorer.

---

## System Architecture

```text
             Chat Data (Mock)
                    │
                    ▼
           Apache Cassandra (Phase 0-1)
                    │
                    ▼
              PySpark ETL (Phase 3)
       - Time Bucketing (bucket_id)
       - Cold Archiver -> Parquet
                    │
                    ▼
               ScyllaDB (Phase 2)
                    │
                    ▼
             NLP Analysis (Phase 4)
       - Vietnamese Text Preprocessing (underthesea)
       - Sentiment Analysis & WordCloud
                    │
                    ▼
   FastAPI & Streamlit Dashboard (Phase 5)
```

---

## Tech Stack

- **Languages & Libraries:** Python 3.x, Pandas, Matplotlib, WordCloud, underthesea (NLP).
- **Databases:** Apache Cassandra (v4.1), ScyllaDB (latest).
- **Big Data Processing:** Apache Spark (PySpark 3.4.x).
- **Infrastructure & Deployment:** Docker, Docker Compose.
- **Backend & Dashboard:** FastAPI, Streamlit.

---

## Local Setup Guide

### 1. Start Docker Cluster
```bash
docker compose up -d
```
Verify that 3 containers are running: `cassandra_source`, `scylla_target`, and `pyspark_workspace`.

### 2. Generate Mock Data (Phase 0)
```bash
docker cp phase_0_setup/generate_mock_data.py pyspark_workspace:/home/jovyan/work/
docker exec -it pyspark_workspace python /home/jovyan/work/generate_mock_data.py
```

### 3. Setup ScyllaDB Schema (Phase 2)
```bash
docker cp phase_2_scylla_design/scylla_ddl_manager.py pyspark_workspace:/home/jovyan/work/
docker exec -it pyspark_workspace python /home/jovyan/work/scylla_ddl_manager.py
```

### 4. Run PySpark ETL (Phase 3)
Run the migration script to transfer data and automatically assign `bucket_id`:
```bash
docker cp phase_3_pyspark_etl/pyspark_etl_migration.py pyspark_workspace:/home/jovyan/work/
docker exec -it -e PYTHONPATH="/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip" pyspark_workspace python /home/jovyan/work/pyspark_etl_migration.py
```

### 5. Run NLP Analysis (Phase 4)
```bash
python3 phase_4_nlp_analysis/nlp_analytics_pipeline.py
```
> If ScyllaDB is not available, run offline: `python3 phase_4_nlp_analysis/nlp_analytics_pipeline.py --offline`

### 6. Launch API & Dashboard (Phase 5)
**Terminal 1 — FastAPI Backend:**
```bash
uvicorn phase_5_dashboard.api:app --reload --host 0.0.0.0 --port 8000
```
**Terminal 2 — Streamlit Dashboard:**
```bash
streamlit run phase_5_dashboard/app.py
```
- Swagger UI: http://localhost:8000/docs
- Dashboard: http://localhost:8501

---

## Troubleshooting

1. **`ModuleNotFoundError: No module named 'pyspark'`**
   - Export the `PYTHONPATH` variable when running `.py` scripts directly inside the Jupyter container (as shown in Step 4).

2. **`SimpleStrategy doesn't support tablet replication` when creating Keyspace on ScyllaDB**
   - Switch to `NetworkTopologyStrategy` with datacenter `'datacenter1'` instead of `SimpleStrategy`.
