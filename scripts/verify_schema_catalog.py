import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import execute_query


CATALOG_FILE = ROOT / "data" / "aaitech_vector_schema_info.csv"


def parse_columns(value):
    if pd.isna(value) or not str(value).strip():
        return set()

    return {
        column.strip().lower()
        for column in str(value).split(",")
        if column.strip()
    }


def get_live_schema():
    sql = """
SELECT
    TABLE_NAME AS table_name,
    COLUMN_NAME AS column_name
FROM information_schema.columns
WHERE table_schema = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION;
"""

    dataframe = execute_query(sql)
    schema = {}

    for table_name, group in dataframe.groupby("table_name"):
        schema[table_name.lower()] = {
            column.lower()
            for column in group["column_name"].tolist()
        }

    return schema


def get_catalog_schema():
    dataframe = pd.read_csv(CATALOG_FILE).fillna("")
    table_rows = dataframe[dataframe["type"].str.lower() == "table"]

    return {
        row["name"].strip().lower(): parse_columns(row["columns"])
        for _, row in table_rows.iterrows()
    }


def main():
    live_schema = get_live_schema()
    catalog_schema = get_catalog_schema()
    has_mismatch = False

    for table_name, catalog_columns in catalog_schema.items():
        live_columns = live_schema.get(table_name)

        if live_columns is None:
            has_mismatch = True
            print(f"[MISSING TABLE] {table_name} is in the catalog but not MySQL.")
            continue

        catalog_only = sorted(catalog_columns - live_columns)
        mysql_only = sorted(live_columns - catalog_columns)

        if catalog_only or mysql_only:
            has_mismatch = True
            print(f"\n[SCHEMA MISMATCH] {table_name}")

            if catalog_only:
                print(f"  Catalog only: {', '.join(catalog_only)}")

            if mysql_only:
                print(f"  MySQL only:   {', '.join(mysql_only)}")

    for table_name in sorted(live_schema.keys() - catalog_schema.keys()):
        has_mismatch = True
        print(f"[UNTRACKED TABLE] {table_name} exists in MySQL but not the catalog.")

    if has_mismatch:
        print("\nSchema verification failed.")
        raise SystemExit(1)

    print("Schema verification passed: catalog matches MySQL.")


if __name__ == "__main__":
    main()