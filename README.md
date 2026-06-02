# DataAI Project 2 — Olist E-Commerce Data Pipeline

End-to-end data engineering pipeline on the Brazilian Olist E-Commerce dataset. Ingests raw CSV data into BigQuery, transforms it through a medallion architecture using dbt, validates with automated tests, and analyses with Python notebooks.

---

## Architecture

```
CSV Files → Python ingestion → BigQuery Bronze → dbt → BigQuery Gold → Jupyter Notebooks
```

**Stack:** BigQuery · dbt · Python · pandas · matplotlib

---

## Project Structure

```
dataAi-project2/
├── ingestion/
│   └── load.py              ← loads all 9 Olist CSVs into BigQuery bronze
├── dbt/
│   └── olist/
│       ├── models/
│       │   ├── fact_orders.sql
│       │   ├── sources.yml
│       │   ├── schema.yml
│       │   └── star/        ← dim_customer, dim_product, dim_seller, dim_date
│       ├── dbt_project.yml
│       ├── profiles.yml
│       └── packages.yml
├── notebooks/
│   ├── monthly_sales.ipynb
│   ├── top_categories.ipynb
│   └── rfm_segmentation.ipynb
├── docs/
│   └── star_schema_design.md
├── environment.yml
├── REPORT.md
└── .gitignore
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/seanwongdev/DataAI-Project2.git
cd DataAI-Project2
```

### 2. Create the conda environment
```bash
conda env create -f environment.yml
conda activate elt
```

### 3. Authenticate with Google Cloud
```bash
gcloud auth application-default login
```

### 4. Download the Olist dataset
Download all CSV files from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place them in:
```
/home/seanwong/code/seanwongeth/data_ai/brazilian-ecommerce/
```

---

## Running the Pipeline

### Step 1 — Ingest raw data into BigQuery Bronze
```bash
python ingestion/load.py
```
Loads 9 CSVs into `dataai-project-0.bronze`. Logs row counts and elapsed time per table.

### Step 2 — Run dbt transformations
```bash
cd dbt/olist
dbt deps          # install dbt packages
dbt run           # build silver and gold models
```

### Step 3 — Run data quality tests
```bash
dbt test
```
Runs 55 tests across all fact and dimension models. Expected: 54 pass, 1 warning (null product categories — known data limitation).

### Step 4 — Generate dbt documentation
```bash
dbt docs generate
dbt docs serve    # opens at localhost:8080
```

### Step 5 — Run analysis notebooks
Open Jupyter and run all cells in each notebook:
```bash
jupyter notebook notebooks/
```

Notebooks (run in any order):
- `monthly_sales.ipynb` — revenue and order volume trends
- `top_categories.ipynb` — top 10 product categories by revenue
- `rfm_segmentation.ipynb` — RFM customer segmentation

---

## Data Quality

55 automated tests covering:
- Primary key uniqueness and not-null constraints on all dimension tables
- Referential integrity between fact_orders and all dimensions
- Mathematical consistency: `total_amount = price + freight_value`
- Value range checks (review scores 1–5, valid date ranges, positive prices)
- Brazilian state code validation
- Row count floor checks on all tables

See `REPORT.md` for full details on data quality issues discovered and resolved.
