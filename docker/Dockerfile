FROM apache/airflow:3.0.2-python3.10

USER root

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    pyarrow \
    pandas \
    requests \
    psycopg2-binary \
    apache-airflow-providers-postgres
