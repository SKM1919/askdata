"""Run one SQL query on the Olist database (read-only) and print the result.
Usage: uv run python src/q.py "SELECT ..."
"""
import sys
import duckdb

con = duckdb.connect("data/olist.duckdb", read_only=True)
print(con.sql(sys.argv[1]))
