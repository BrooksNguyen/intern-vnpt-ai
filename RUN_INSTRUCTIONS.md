# 🚀 System Run Instructions

This document provides detailed steps to launch the entire Big Data system and Dashboard (from Phase 0 to Phase 5) in a local environment.

## 🛠️ 1. Prerequisites
- **Docker** and **Docker Compose** installed.
- **Python 3.9+** installed.
- Required Python libraries installed:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🏗️ 2. Launch Database & Spark Cluster (Docker)
The system cluster uses Docker to run Cassandra (Source), ScyllaDB (Target), and Apache Spark.
From the project root directory, open a Terminal and run:
```bash
docker compose up -d
```
Wait approximately 30-60 seconds for the containers to fully start. You can check the status using the `docker ps` command (ensure that the 3 containers `cassandra_source`, `scylla_target`, and `pyspark_workspace` are in the **Up** state).

---

## ⚡ 3. Run the Entire Pipeline via 1-Click (Phase 0 ➔ 4)
For simplicity, the project provides a shell script that fully automates the entire ETL flow and NLP Analysis.

Run the following command on your host Terminal:
```bash
bash run_pipeline.sh
```

**This script automatically performs these steps:**
1. **Mock Data Generation:** Generates synthetic chat data and pushes it to Cassandra (Phase 0).
2. **Database Initialization:** Creates the Keyspace and Table (with Time-bucketing) on ScyllaDB (Phase 2).
3. **PySpark ETL Execution:** Migrates, transforms (calculating `bucket_id`), and parallel writes data from Cassandra to ScyllaDB via the Spark container (Phase 3).
4. **EDA Chart Generation:** Visualizes post-migration data (Phases 1 & 3).
5. **NLP Analysis Execution:** Preprocesses text, generates Keywords, WordCloud, and sentiment charts (Phase 4).

> **Note:** If you prefer not to start Docker (or have limited hardware resources), you can independently test the NLP feature using Mock Data via this command: `python3 phase_4_nlp_analysis/nlp_analytics_pipeline.py --offline`

---

## 🖥️ 4. Launch Backend API & Dashboard (Phase 5)

Once the data is safely stored in ScyllaDB, you can launch the API and UI.
You need to open **2 new Terminal Tabs**.

### Terminal 1: Run FastAPI Backend
The Backend API queries data from ScyllaDB and supports Backtracking Pagination.
```bash
uvicorn phase_5_dashboard.api:app --reload --host 0.0.0.0 --port 8000
```
- Access auto-generated API documentation (Swagger UI): **http://localhost:8000/docs**

### Terminal 2: Run Streamlit Dashboard
An interactive Web UI displaying NLP charts, database schema information, and Chat API testing tools.
```bash
streamlit run phase_5_dashboard/app.py
```
- Your browser will automatically open the Dashboard at: **http://localhost:8501**

---

## 🛑 5. Cleanup and Teardown
When finished, to shut down the system and free up RAM/CPU resources, run:
```bash
docker compose down
```
*(If you want to wipe all database data to start fresh, run `docker compose down -v` to delete the Docker Volumes as well).*
