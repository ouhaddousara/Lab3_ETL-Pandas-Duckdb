# Lab 3 — ETL Pipeline with Pandas & DuckDB

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-latest-yellow?logo=duckdb&logoColor=black)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

## Overview

A complete **ETL (Extract, Transform, Load)** pipeline built from scratch using **Pandas** for data cleaning and transformation, and **DuckDB** as an in-process analytical database for SQL querying.

The pipeline processes synthetic e-commerce data (orders + customers), applies a full cleaning workflow, and produces analytical reports exported as CSV files.

---

## Project Structure

```
lab3/
├── data/
│   ├── raw_orders.csv        # Generated raw orders data
│   └── raw_customers.csv     # Generated raw customers data
├── output/
│   ├── sales_by_country.csv  # Total sales aggregated by country
│   ├── monthly_sales.csv     # Monthly sales trend
│   └── top5_customers.csv    # Top 5 customers by total spend
├── lab3_etl.py               # Main ETL script
├── .gitignore
└── README.md
```
---


## Tech Stack

| Tool | Role |
|---|---|
| Python 3.10+ | Core language |
| Pandas | Data cleaning & transformation |
| DuckDB | In-process SQL analytics |
| NumPy | Numerical operations |
| Faker | Synthetic data generation |

---

## Getting Started

### Prerequisites

```bash
pip install pandas duckdb numpy faker
```

### Run the pipeline

```bash
python3 lab3_etl.py
```

---

## ETL Pipeline

### 1. Extract
- Synthetic data generated programmatically (orders + customers)
- Loaded into Pandas DataFrames and DuckDB tables

### 2. Transform (Pandas)

| Step | Technique | Column |
|---|---|---|
| Missing values | Median imputation / constant fill | `amount`, `country` |
| Duplicates | `drop_duplicates()` | All |
| Outliers | IQR method (1.5×IQR) | `amount` |
| Normalization | Min-Max scaling | `amount` → `amount_normalized` |
| Encoding | Label Encoding | `country` → `country_encoded` |
| Feature selection | Column subset | Both DataFrames |
| Date parsing | `pd.to_datetime()` | `order_date` → `order_month` |

### 3. Load
- Cleaned & merged DataFrame loaded into DuckDB as `merged_clean` table

---

## Analytical Queries (DuckDB SQL)

```sql
-- Total sales by country
SELECT country, COUNT(order_id) AS nb_orders, ROUND(SUM(amount), 2) AS total_sales
FROM merged_clean GROUP BY country ORDER BY total_sales DESC;

-- Monthly sales
SELECT order_month, COUNT(order_id) AS nb_orders, ROUND(SUM(amount), 2) AS total_sales
FROM merged_clean GROUP BY order_month ORDER BY order_month;

-- Top 5 customers by total spend
SELECT customer_id, name, country, COUNT(order_id) AS nb_orders, ROUND(SUM(amount), 2) AS total_spent
FROM merged_clean GROUP BY customer_id, name, country ORDER BY total_spent DESC LIMIT 5;
```

---

## Sample Results

**Total sales by country**
| Country | Orders | Total Sales |
|---|---|---|
| Germany | 38 | 5156.78 |
| UK | 27 | 3423.65 |
| France | 25 | 3368.18 |

**Top 5 Customers**
| Name | Country | Orders | Total Spent |
|---|---|---|---|
| Christopher Mcknight | Germany | 6 | 1149.11 |
| Tyler Nash | USA | 8 | 1010.31 |
| Sara Ramos | UK | 4 | 966.76 |

---

## Output Files

| File | Description |
|---|---|
| `sales_by_country.csv` | Aggregated revenue per country |
| `monthly_sales.csv` | Month-over-month sales trend |
| `top5_customers.csv` | Highest-value customers |

---

> **Note:** The `data/` and `output/` folders are not included in the repository.
> They are automatically generated when you run `python3 lab3_etl.py`.

---


## Author

**Sara Ouhaddou**  - Data Engineering Student  
[![GitHub](https://img.shields.io/badge/GitHub-ouhaddousara-black?logo=github)](https://github.com/ouhaddousara)
