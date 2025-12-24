CREATE SCHEMA IF NOT EXISTS taxi;

CREATE TABLE IF NOT EXISTS taxi.pipeline_metadata (
  pipeline_name text PRIMARY KEY,
  last_loaded_month date,
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Raw landing (Bronze)
CREATE TABLE IF NOT EXISTS taxi.raw_yellow_tripdata (
  id bigserial PRIMARY KEY,
  source_month date NOT NULL,
  source_file text NOT NULL,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL
);

-- Optional: prevent double-loading the exact same file/month
CREATE UNIQUE INDEX IF NOT EXISTS ux_raw_yellow_month_file
ON taxi.raw_yellow_tripdata (source_month, source_file, id);
