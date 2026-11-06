## Add your own just recipes here. This is imported by the main justfile.

# Overriding recipes from the root justfile by adding a recipe with the same
# name in this file is not possible until a known issue in just is fixed,
# https://github.com/casey/just/issues/2540

# Load the Attribute and Measurement examples into DuckDB and print the tables (prototype)
attribute-duckdb:
  uv run --with duckdb python -m ber_central_schema.attribute_tables
