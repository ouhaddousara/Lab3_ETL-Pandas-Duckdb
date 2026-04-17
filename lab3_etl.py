import pandas as pd
import duckdb
import numpy as np
import os
from faker import Faker


fake = Faker()
os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Generating data for the two CSV Files (raw orders.csv ,raw customers.csv)


#Generation of raw_customers.csv 

np.random.seed(42)
n_customers = 50
customer_ids = list(range(101, 101 + n_customers))
countries = ["USA", "Canada", "France", "Germany", "Morocco", "Brazil", "UK"]

customers_data = {
    "customer_id": customer_ids,
    "name": [fake.name() for _ in range(n_customers)],
    "country": np.random.choice(countries, n_customers),
}
df_customers_raw = pd.DataFrame(customers_data)


df_customers_raw = pd.concat(
    [df_customers_raw, df_customers_raw.sample(5, random_state=1)], ignore_index=True
)

df_customers_raw.loc[np.random.choice(df_customers_raw.index, 5), "country"] = np.nan

df_customers_raw.to_csv("data/raw_customers.csv", index=False)
print("raw_customers.csv generated")

#Generation of raw_orders.csv 

n_orders = 200
orders_data = {
    "order_id": range(1, n_orders + 1),
    "customer_id": np.random.choice(customer_ids, n_orders),
    "order_date": pd.date_range("2024-01-01", periods=n_orders, freq="2D").strftime("%Y-%m-%d"),
    "amount": np.round(np.random.exponential(scale=150, size=n_orders), 2),
}
df_orders_raw = pd.DataFrame(orders_data)


df_orders_raw = pd.concat(
    [df_orders_raw, df_orders_raw.sample(10, random_state=2)], ignore_index=True
)
df_orders_raw.loc[np.random.choice(df_orders_raw.index, 8), "amount"] = np.nan
df_orders_raw.loc[np.random.choice(df_orders_raw.index, 3), "amount"] = 99999  # outliers

df_orders_raw.to_csv("data/raw_orders.csv", index=False)
print("raw_orders.csv generated")


# 1. Load Raw Data, using pandas and duckdb

# Loading with Pandas 

df_orders = pd.read_csv("data/raw_orders.csv")
df_customers = pd.read_csv("data/raw_customers.csv")

# ── Loading with DuckDB 

con = duckdb.connect() 
con.execute("CREATE TABLE orders AS SELECT * FROM read_csv_auto('data/raw_orders.csv')")
con.execute("CREATE TABLE customers AS SELECT * FROM read_csv_auto('data/raw_customers.csv')")

print("\n Data loaded into DuckDB:")
print(con.execute("SELECT COUNT(*) as nb_orders FROM orders").fetchdf())
print(con.execute("SELECT COUNT(*) as nb_customers FROM customers").fetchdf())


# 2. show info , describe , shape

print("\n 1. ORDERS")
print(f"Shape     : {df_orders.shape}")
print("\ninfo")
df_orders.info()
print("\ndescribe")
print(df_orders.describe())

print("\n 2. CUSTOMERS")
print(f"Shape     : {df_customers.shape}")
df_customers.info()
print(df_customers.describe(include="all"))


# 3. Clean and Transform with Pandas


print(f"\n Missing values before:\n{df_orders.isnull().sum()}")
df_orders["amount"] = df_orders["amount"].fillna(df_orders["amount"].median())
df_customers["country"] = df_customers["country"].fillna("Unknown")
print(f" Missing values after:\n{df_orders.isnull().sum()}")



print(f"\n Duplicate orders  : {df_orders.duplicated().sum()}")
print(f" Duplicate customers: {df_customers.duplicated().sum()}")
df_orders.drop_duplicates(inplace=True)
df_customers.drop_duplicates(inplace=True)
df_orders.reset_index(drop=True, inplace=True)
df_customers.reset_index(drop=True, inplace=True)
print(" Duplicates removed")



Q1 = df_orders["amount"].quantile(0.25)
Q3 = df_orders["amount"].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
outliers_mask = (df_orders["amount"] < lower) | (df_orders["amount"] > upper)
print(f"\n Detected outliers : {outliers_mask.sum()}")
df_orders = df_orders[~outliers_mask].reset_index(drop=True)
print(f" Outliers removed. Final shape orders: {df_orders.shape}")



df_orders["amount_normalized"] = (
    (df_orders["amount"] - df_orders["amount"].min())
    / (df_orders["amount"].max() - df_orders["amount"].min())
)
print("\n Min-Max normalization applied on 'amount'")



df_customers["country_encoded"] = df_customers["country"].astype("category").cat.codes
print("\n 'country' Encoding:")
print(df_customers[["country", "country_encoded"]].drop_duplicates().sort_values("country_encoded"))


df_orders = df_orders[["order_id", "customer_id", "order_date", "amount", "amount_normalized"]]
df_customers = df_customers[["customer_id", "name", "country", "country_encoded"]]
print(" Feature selection performed")


df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
df_orders["order_month"] = df_orders["order_date"].dt.to_period("M").astype(str)



# 4. Merge the two DataSets into one merged DataSet

df_merged = pd.merge(df_orders, df_customers, on="customer_id", how="left")
print(f"\n Merged dataset: {df_merged.shape}")
print(df_merged.head(3))


# 5. Load Cleaned Data into DuckDB

con.execute("DROP TABLE IF EXISTS merged_clean")
con.execute("CREATE TABLE merged_clean AS SELECT * FROM df_merged")
print("\n Table 'merged_clean' loaded into DuckDB")
print(con.execute("SELECT COUNT(*) as total FROM merged_clean").fetchdf())

# 6. Run Analytical Queries with DuckDB 

# 6.1 • create SQL query that returns Total sales by country

sales_by_country = con.execute("""
    SELECT
        country,
        COUNT(order_id)       AS nb_orders,
        ROUND(SUM(amount), 2) AS total_sales
    FROM merged_clean
    GROUP BY country
    ORDER BY total_sales DESC
""").fetchdf()

print("\n Total sales by country:")
print(sales_by_country)

# 6.2 • create SQL query that returns Monthly sales

monthly_sales = con.execute("""
    SELECT
        order_month,
        COUNT(order_id)       AS nb_orders,
        ROUND(SUM(amount), 2) AS total_sales
    FROM merged_clean
    GROUP BY order_month
    ORDER BY order_month
""").fetchdf()

print("\n Monthly sales:")
print(monthly_sales)

# 6.3 • create SQL query that returns Top 5 customers by total spend

top5_customers = con.execute("""
    SELECT
        customer_id,
        name,
        country,
        COUNT(order_id)       AS nb_orders,
        ROUND(SUM(amount), 2) AS total_spent
    FROM merged_clean
    GROUP BY customer_id, name, country
    ORDER BY total_spent DESC
    LIMIT 5
""").fetchdf()

print("\n Top 5 customers by total spend:")
print(top5_customers)

# 7. Save Results Back to Files, in 3 different CSV files


sales_by_country.to_csv("output/sales_by_country.csv", index=False)
monthly_sales.to_csv("output/monthly_sales.csv", index=False)
top5_customers.to_csv("output/top5_customers.csv", index=False)

print("\n Results saved to output/")
print("   ├── sales_by_country.csv")
print("   ├── monthly_sales.csv")
print("   └── top5_customers.csv")

con.close()
print("\n Lab 3 completed successfully!")