import csv
import logging
import tempfile
import time
from pathlib import Path

import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

# Files whose free-text fields contain unescaped quotes that break BigQuery's
# strict CSV parser — pandas handles these and rewrites them as valid CSV.
NEEDS_CLEANING = {"olist_order_reviews_dataset.csv"}

PROJECT_ID = "dataai-project-0"
DATASET = "bronze"
DATA_DIR = Path("/home/seanwong/code/seanwongeth/data_ai/brazilian-ecommerce")

TABLES = {
    "raw_orders": "olist_orders_dataset.csv",
    "raw_customers": "olist_customers_dataset.csv",
    "raw_products": "olist_products_dataset.csv",
    "raw_sellers": "olist_sellers_dataset.csv",
    "raw_order_items": "olist_order_items_dataset.csv",
    "raw_order_payments": "olist_order_payments_dataset.csv",
    "raw_order_reviews": "olist_order_reviews_dataset.csv",
    "raw_geolocation": "olist_geolocation_dataset.csv",
    "raw_product_category_translation": "product_category_name_translation.csv",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def create_dataset(client: bigquery.Client) -> None:
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    dataset_ref.location = "US"
    try:
        client.create_dataset(dataset_ref)
        log.info("Created dataset %s.%s", PROJECT_ID, DATASET)
    except Conflict:
        log.info("Dataset %s.%s already exists", PROJECT_ID, DATASET)


def clean_csv(csv_path: Path) -> Path:
    """Read a malformed CSV with pandas, strip embedded newlines and quotes from
    free-text fields, then write a properly quoted temp file for BigQuery."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig", on_bad_lines="warn")
    for col in df.select_dtypes(include="object").columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("\r\n", " ", regex=False)
            .str.replace("\n", " ", regex=False)
            .str.replace("\r", " ", regex=False)
            .str.replace('"', "'", regex=False)
        )
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    df.to_csv(tmp, index=False, quoting=csv.QUOTE_ALL)
    tmp.close()
    log.info("Cleaned %s → %s (%d rows)", csv_path.name, tmp.name, len(df))
    return Path(tmp.name)


def load_table(client: bigquery.Client, table_name: str, csv_file: str) -> int:
    csv_path = DATA_DIR / csv_file
    if not csv_path.exists():
        log.error("File not found: %s — skipping", csv_path)
        return 0

    if csv_file in NEEDS_CLEANING:
        load_path = clean_csv(csv_path)
    else:
        load_path = csv_path

    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
    )

    t0 = time.time()
    with open(load_path, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
    job.result()
    elapsed = time.time() - t0

    if csv_file in NEEDS_CLEANING:
        load_path.unlink()

    loaded = client.get_table(table_id).num_rows
    log.info("%s: %d rows loaded in %.1fs", table_name, loaded, elapsed)
    return loaded


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    create_dataset(client)

    total = 0
    errors = []
    for table_name, csv_file in TABLES.items():
        try:
            total += load_table(client, table_name, csv_file)
        except Exception as e:
            log.error("%s: failed — %s", table_name, e)
            errors.append(table_name)

    log.info("Done. Total rows loaded: %d", total)
    if errors:
        log.error("Failed tables: %s", errors)


if __name__ == "__main__":
    main()
