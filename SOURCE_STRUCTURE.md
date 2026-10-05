# 📂 Project Source Structure

The project is divided into **6 main directories (Phase 0 to Phase 5)** corresponding to the internship roadmap, along with configuration files and automation scripts located in the root directory.

## 🗂️ Root Directory
- **`docker-compose.yml`**: Docker Compose configuration file to launch the service cluster consisting of Cassandra (Source), ScyllaDB (Target), and PySpark.
- **`run_pipeline.sh`**: A bash script that bundles the entire process (Generate mock data ➔ Initialize Schema ➔ Run PySpark ETL ➔ Generate charts ➔ Run NLP) for one-click execution.
- **`requirements.txt`**: List of all required Python libraries (Dependencies) for the project.
- **`schema.cql`**: DDL (Data Definition Language) file containing commands to initialize the Keyspace and Table on ScyllaDB (with TTL and gc_grace_seconds configurations).
- **`gen_real_charts.py`**: A script that connects directly to the databases (Cassandra/ScyllaDB) to visualize data post-migration.

---

## 🗂️ 1. `phase_0_setup/` (Data Generation & Initialization)
Contains scripts for environment setup and initial mock data generation.
- **`generate_mock_data.py`**: Randomly generates synthetic chat data and pushes it directly into Cassandra. Simulates the "Hot Partition" phenomenon at `room_999` to support the optimization problem.

---

## 🗂️ 2. `phase_1_profiling/` (Exploratory Data Analysis - EDA)
Contains notebooks and scripts used to analyze current data conditions.
- **`eda_plot.py`**: Generates charts from partitioned data to analyze and evaluate bottleneck conditions at the partition level.

---

## 🗂️ 3. `phase_2_scylla_design/` (ScyllaDB Database Design)
Data Modeling optimization and Time-bucketing application.
- **`scylla_ddl_manager.py`**: Connects and executes CQL commands to create new tables on ScyllaDB, applying an advanced Primary Key structure: `((room_id, bucket_id), message_id)` to partition data by month.

---

## 🗂️ 4. `phase_3_pyspark_etl/` (ETL Data Pipeline)
Large-scale data transformation and storage pipeline.
- **`pyspark_etl_migration.py`**: PySpark script that reads data from Cassandra, processes logic to add a `bucket_id` column based on the timestamp, and performs parallel batch writes to ScyllaDB.
- **`cold_archiver.py`**: PySpark script utilizing *Partition Pruning* to automatically scan and compress cold/old data into Parquet format for Cold Storage.

---

## 🗂️ 5. `phase_4_nlp_analysis/` (Natural Language Processing)
Extracts actionable insights from chat messages.
- **`nlp_analytics_pipeline.py`**: Comprehensive pipeline integrating the `underthesea` library for Vietnamese text preprocessing. Performs Sentiment Analysis, generates Top 50 Keywords, and draws WordClouds. Supports an `--offline` mode with mock data generation.
- **`stopwords.txt`**: Custom Vietnamese stopwords dictionary for the chat system.

---

## 🗂️ 6. `phase_5_dashboard/` (API & Dashboard Interface)
Data visualization for end-users and Mentors.
- **`api.py`**: Web Backend service built with **FastAPI**, providing a `/messages` endpoint supporting Pagination for fast querying from ScyllaDB.
- **`backend_service.py`**: Core ScyllaDB querying logic, highlighting the **Backtracking Pagination** algorithm (automatically backtracking to previous months if the current bucket lacks sufficient data).
- **`app.py`**: Web Frontend interface built with **Streamlit**. Integrates schema displays, sentiment charts, WordClouds, ETL Pipeline visualizations, a chat box, and Lessons Learned summaries into 5 intuitive, professional Tabs.

---

## 🗂️ Supporting Directories
- **`Intern_Guide/`**: Complete operational guidelines and problem requirements from Mentors for the internship weeks.
- **`overleaf_report/`**: LaTeX source code for the final internship specialized report, synced with the output results (images, tables).
