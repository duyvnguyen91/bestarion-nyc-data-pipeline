from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta

import requests
import pyarrow.parquet as pq
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_values


POSTGRES_CONN_ID = "postgres_datalake"
TARGET_TABLE = "raw_taxi_data_2025"
DATASET = "yellow"                              # yellow | green | fhvhv | fhv
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

# Columns in your raw_taxi_data_2025 table
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
    for month in range(1, 12):  # 1..11
        ym = f"2025-{month:02d}"
        filename = f"{ds}_tripdata_{ym}.parquet"
        url = f"{BASE_URL}/{filename}"
        urls.append((url, filename))
    return urls


def download_parquet(**context) -> str:
    urls = file_urls_2025_jan_to_nov(DATASET)

    for url, filename in urls:
        head = requests.head(url, timeout=30)
        if head.status_code != 200:
            continue  # skip missing month

        # download
        tmp_dir = tempfile.mkdtemp(prefix="nyc_taxi_")
        out_path = os.path.join(tmp_dir, filename)

        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8 * 1024 * 1024):
                    if chunk:
                        f.write(chunk)

        # load into postgres
        load_into_postgres(out_path)


def load_into_postgres(parquet_path: str) -> None:
    """
    Read ONE parquet file -> insert into Postgres raw table.
    Ignores extra columns not in TARGET_TABLE.
    """
    if not parquet_path or not os.path.exists(parquet_path):
        raise RuntimeError(f"Parquet file not found: {parquet_path}")

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    pf = pq.ParquetFile(parquet_path)

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

    # reverse map: target_col -> source_col
    target_to_source = {tgt: src for src, tgt in name_map.items()}

    batch_size = 50000
    page_size = 5000

    for batch in pf.iter_batches(batch_size=batch_size):
        tbl = batch.to_pydict()
        if not tbl:
            continue

        n = len(next(iter(tbl.values())))
        rows = []

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
    "retries": 1,
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
