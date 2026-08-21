#!/bin/bash
set -e

echo "Running mock data generator..."
python3 phase_0_setup/generate_mock_data.py

echo "Setting up ScyllaDB schema..."
SCYLLA_HOST=127.0.0.1 SCYLLA_PORT=9043 python3 phase_2_scylla_design/scylla_ddl_manager.py

echo "Running ETL migration (Docker)..."
docker exec -e CASSANDRA_HOST=cassandra_source \
    -e CASSANDRA_PORT=9042 \
    -e SCYLLA_HOST=scylla_target \
    -e SCYLLA_PORT=9042 \
    pyspark_workspace \
    spark-submit --packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 \
    /home/jovyan/work/phase_3_pyspark_etl/pyspark_etl_migration.py --mode optimized

echo "Generating charts..."
python3 gen_real_charts.py

echo "Running text preprocessing..."
python3 phase_4_nlp_analysis/text_preprocessing.py

echo "Done"
