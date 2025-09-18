import pandas as pd
import sqlite3
import sys

INPUT_CSV = 'agora_testing_set.csv'
DB_FILE = 'agora_test.db'
TABLE_NAME = 'listings'

print(f"--- Creating SQLite Database from {INPUT_CSV} ---")

try:
    # Load the CSV with encoding fallback
    try:
        df = pd.read_csv(INPUT_CSV, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(INPUT_CSV, encoding='latin-1')

    # Clean up column names just in case
    df.rename(columns=lambda x: x.strip(), inplace=True)
    if 'Item Descr' in df.columns:
        df.rename(columns={'Item Descr': 'Item Description'}, inplace=True)

    # Connect to the SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect(DB_FILE)

    # Write the pandas DataFrame to the SQLite table
    print(f"Writing data to table '{TABLE_NAME}'...")
    df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)

    # --- CRITICAL EFFICIENCY STEP ---
    # Create an index on the 'Vendor' column for super-fast lookups
    print("Creating index on 'Vendor' column for fast searching...")
    conn.execute(f"CREATE INDEX idx_vendor ON {TABLE_NAME} (Vendor);")

    conn.close()

    print(f"\n--- Success! Database '{DB_FILE}' created successfully. ---")

except FileNotFoundError:
    print(f"FATAL ERROR: The file '{INPUT_CSV}' was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")