from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta

import requests
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from psycopg2.extras import execute_values


# =========================================================
# CONFIG
# =========================================================

POSTGRES_CONN_ID = "postgres_datalake"

RAW_TABLE = "raw_taxi_data_2025"
SILVER_TABLE = "silver_taxi_trips"
GOLD_TABLE = "gold_daily_metrics"

DATASET = "yellow"  # yellow | green | fhv | fhvhv
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


TABLE_COLUMNS = [
    "vendor_id",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "ratecode_id",
    "store_and_fwd_flag",
    "pu_location_id",
    "do_location_id",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "congestion_surcharge",
    "airport_fee",
]

def file_urls_2025_jan_to_nov(ds: str) -> list[tuple[str, str]]:
    urls = []
    for month in range(9, 12):  # adjust if needed
        ym = f"2025-{month:02d}"
        filename = f"{ds}_tripdata_{ym}.parquet"
        urls.append((f"{BASE_URL}/{filename}", filename))
    return urls

def download_parquet(**context):
    urls = file_urls_2025_jan_to_nov(DATASET)
    parquet_paths = []

    for url, filename in urls:
        head = requests.head(url, timeout=30)
        if head.status_code != 200:
            continue

        tmp_dir = tempfile.mkdtemp(prefix="nyc_taxi_")
        out_path = os.path.join(tmp_dir, filename)

        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8 * 1024 * 1024):
                    if chunk:
                        f.write(chunk)

        parquet_paths.append(out_path)

    context["ti"].xcom_push(key="parquet_paths", value=parquet_paths)

def load_into_postgres(**context):
    parquet_paths = context["ti"].xcom_pull(
        task_ids="download_parquet",
        key="parquet_paths"
    )

    if not parquet_paths:
        raise RuntimeError("No parquet files to load")

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    name_map = {
        "VendorID": "vendor_id",
        "tpep_pickup_datetime": "tpep_pickup_datetime",
        "tpep_dropoff_datetime": "tpep_dropoff_datetime",
        "passenger_count": "passenger_count",
        "trip_distance": "trip_distance",
        "RatecodeID": "ratecode_id",
        "store_and_fwd_flag": "store_and_fwd_flag",
        "PULocationID": "pu_location_id",
        "DOLocationID": "do_location_id",
        "payment_type": "payment_type",
        "fare_amount": "fare_amount",
        "extra": "extra",
        "mta_tax": "mta_tax",
        "tip_amount": "tip_amount",
        "tolls_amount": "tolls_amount",
        "improvement_surcharge": "improvement_surcharge",
        "total_amount": "total_amount",
        "congestion_surcharge": "congestion_surcharge",
        "airport_fee": "airport_fee",
    }

    target_to_source = {tgt: src for src, tgt in name_map.items()}

    insert_sql = f"""
        INSERT INTO {RAW_TABLE} ({", ".join(TABLE_COLUMNS)})
        VALUES %s
    """

    conn = hook.get_conn()
    cur = conn.cursor()

    for parquet_path in parquet_paths:
        pf = pq.ParquetFile(parquet_path)

        for batch in pf.iter_batches(batch_size=50000):
            tbl = batch.to_pydict()
            if not tbl:
                continue

            rows = []
            n = len(next(iter(tbl.values())))

            for i in range(n):
                row = [
                    tbl[target_to_source[col]][i]
                    if target_to_source.get(col) in tbl
                    else None
                    for col in TABLE_COLUMNS
                ]
                rows.append(tuple(row))

            execute_values(cur, insert_sql, rows, page_size=5000)
            conn.commit()

    cur.close()
    conn.close()

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="nyc_taxi_raw_ingest_2025",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["nyc", "taxi", "bronze", "silver", "gold"],
) as dag:

    create_raw_table = SQLExecuteQueryOperator(
        task_id="create_raw_table",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"""
        CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
            vendor_id INTEGER,
            tpep_pickup_datetime TIMESTAMP,
            tpep_dropoff_datetime TIMESTAMP,
            passenger_count INTEGER,
            trip_distance NUMERIC,
            ratecode_id INTEGER,
            store_and_fwd_flag TEXT,
            pu_location_id INTEGER,
            do_location_id INTEGER,
            payment_type INTEGER,
            fare_amount NUMERIC,
            extra NUMERIC,
            mta_tax NUMERIC,
            tip_amount NUMERIC,
            tolls_amount NUMERIC,
            improvement_surcharge NUMERIC,
            total_amount NUMERIC,
            congestion_surcharge NUMERIC,
            airport_fee NUMERIC
        );
        """
    )

    download_task = PythonOperator(
        task_id="download_parquet",
        python_callable=download_parquet,
    )

    load_raw = PythonOperator(
        task_id="load_into_postgres",
        python_callable=load_into_postgres,
        retries=0,
    )

    transform_silver = SQLExecuteQueryOperator(
        task_id="transform_to_silver",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"""
        CREATE TABLE IF NOT EXISTS {SILVER_TABLE} AS
        SELECT
            vendor_id,
            tpep_pickup_datetime,
            tpep_dropoff_datetime,
            DATE(tpep_pickup_datetime) AS pickup_date,
            passenger_count,
            trip_distance,
            pu_location_id,
            do_location_id,
            total_amount
        FROM {RAW_TABLE}
        WHERE trip_distance > 0
          AND total_amount > 0;
        """
    )

    aggregate_gold = SQLExecuteQueryOperator(
        task_id="aggregate_to_gold",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"""
        CREATE TABLE IF NOT EXISTS {GOLD_TABLE} AS
        SELECT
            pickup_date,
            COUNT(*) AS trips,
            SUM(total_amount) AS revenue,
            AVG(trip_distance) AS avg_distance
        FROM {SILVER_TABLE}
        GROUP BY pickup_date;
        """
    )

    (
        create_raw_table
        >> download_task
        >> load_raw
        >> transform_silver
        >> aggregate_gold
    )
