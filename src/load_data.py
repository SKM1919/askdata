"""Load the 9 Olist CSV files into one DuckDB database file."""
import duckdb, glob, os

con = duckdb.connect("data/olist.duckdb")

for f in sorted(glob.glob("data/*.csv")):
    name = (os.path.basename(f)
            .replace("olist_", "")
            .replace("_dataset.csv", "")
            .replace(".csv", ""))
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto('{f}')")
    rows = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"{name:40} {rows:>10,} rows")

con.close()
print("Done. Database saved to data/olist.duckdb")
