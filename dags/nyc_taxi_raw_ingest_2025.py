from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta

import requests
import pyarrow.parquet as pq
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_values


# ====== CONFIG YOU MAY CHANGE ======
POSTGRES_CONN_ID = "postgres_datalake"          # Airflow Connection ID
TARGET_TABLE = "raw_taxi_data_2025"             # your table in Postgres
DATASET = "yellow"                              # yellow | green | fhvhv | fhv
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
# TLC hosts monthly parquet trip files (see TLC Trip Record Data page) :contentReference[oaicite:1]{index=1}

# Columns in your raw_taxi_data_2025 table (adjust if your table differs)
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
# ===================================


def _file_url(ds: str, year: int, month: int) -> tuple[str, str]:
    ym = f"{year:04d}-{month:02d}"
    filename = f"{ds}_tripdata_{ym}.parquet"
    return f"{BASE_URL}/{filename}", filename


def download_parquet(**context) -> str:
    """
    Download parquet for the execution month (data interval start).
    """
    # Use Airflow logical date to decide which month to load
    logical_date = context["logical_date"]
    year = logical_date.year
    month = logical_date.month

    url, filename = _file_url(DATASET, year, month)

    tmp_dir = tempfile.mkdtemp(prefix="nyc_taxi_")
    out_path = os.path.join(tmp_dir, filename)

    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
            if chunk:
                f.write(chunk)

    context["ti"].xcom_push(key="parquet_path", value=out_path)
    context["ti"].xcom_push(key="source_url", value=url)
    return out_path


def load_into_postgres(**context) -> None:
    """
    Read parquet -> insert into Postgres raw table.
    Ignores extra columns not in TARGET_TABLE.
    """
    parquet_path = context["ti"].xcom_pull(task_ids="download_parquet", key="parquet_path")
    if not parquet_path or not os.path.exists(parquet_path):
        raise RuntimeError("Parquet file not found from XCom.")

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    # Optional: full refresh per run-month (safe for demo)
    # If you want incremental append, remove this TRUNCATE and add a unique key strategy instead.
    hook.run(f"TRUNCATE TABLE {TARGET_TABLE};")

    pf = pq.ParquetFile(parquet_path)

    # TLC parquet columns are often CamelCase (VendorID, PULocationID, etc.)
    # We map common TLC names -> your snake_case columns.
    # If a column doesn't exist, insert NULL.
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

    conn = hook.get_conn()
    cur = conn.cursor()

    insert_sql = f"""
        INSERT INTO {TARGET_TABLE} ({", ".join(TABLE_COLUMNS)})
        VALUES %s
    """

    # Insert in batches
    batch_size = 50000
    page_size = 5000

    for batch in pf.iter_batches(batch_size=batch_size):
        tbl = batch.to_pydict()

        # Build rows in the exact TABLE_COLUMNS order
        rows = []
        # Determine source keys per target col
        # reverse map: target -> source key (first match)
        target_to_source = {}
        for src, tgt in name_map.items():
            target_to_source[tgt] = src

        n = len(next(iter(tbl.values()))) if tbl else 0
        for i in range(n):
            row = []
            for col in TABLE_COLUMNS:
                src_key = target_to_source.get(col)
                if src_key and src_key in tbl:
                    row.append(tbl[src_key][i])
                else:
                    row.append(None)
            rows.append(tuple(row))

        execute_values(cur, insert_sql, rows, page_size=page_size)
        conn.commit()

    cur.close()
    conn.close()


default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="nyc_taxi_raw_ingest_2025",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@monthly",   # runs once per month
    catchup=False,         # set True if you want to backfill months
    max_active_runs=1,
    tags=["nyc", "taxi", "raw", "postgres"],
) as dag:

    t1 = PythonOperator(
        task_id="download_parquet",
        python_callable=download_parquet,
    )

    t2 = PythonOperator(
        task_id="load_into_postgres",
        python_callable=load_into_postgres,
    )

    t1 >> t2
