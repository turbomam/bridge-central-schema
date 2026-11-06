"""Load the Attribute, Measurement, Sample and SequenceFeature examples into DuckDB.

A prototype loader for docs/attribute-measurement-design.md. Every Attribute and
Measurement, whether it is a file of its own or an entry in a Sample's or a
SequenceFeature's attributes, becomes one row of the table attribute_value. Its columns
are Measurement's slots, which include all of Attribute's, plus where the row came from:
parent_class and parent_id (empty for a file of its own) and position in the parent's
list. tbd_type_designator says which class each row is.

Usage:
    uv run --with duckdb python -m ber_central_schema.attribute_tables [--db FILE] [DIR]

DIR defaults to tests/data/valid. Prints each table.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import yaml
from linkml_runtime import SchemaView

PACKAGE = Path(__file__).resolve().parent
SCHEMA = PACKAGE / "schema" / "ber_central_schema.yaml"
SQL_TYPES = {"double": "DOUBLE", "float": "DOUBLE", "integer": "BIGINT"}


def columns(view: SchemaView) -> dict[str, str]:
    """Measurement's slots, in schema order, with a DuckDB type for each."""
    return {
        slot.name: SQL_TYPES.get(slot.range, "VARCHAR")
        for slot in view.class_induced_slots("Measurement")
    }


def rows(directory: Path):
    """Yield (source_file, parent_class, parent_id, position, entry) for every Attribute and Measurement."""
    for path in sorted(directory.glob("*.yaml")):
        cls = path.stem.split("-")[0]
        data = yaml.safe_load(path.read_text())
        if cls in ("Attribute", "Measurement"):
            yield path.name, None, None, None, data
        elif cls in ("Sample", "SequenceFeature"):
            parent_id = data.get("id") or data.get("feature_id")
            for position, entry in enumerate(data.get("attributes") or []):
                yield path.name, cls, parent_id, position, entry
        elif cls == "Dataset":
            for feature in data.get("features") or []:
                for position, entry in enumerate(feature.get("attributes") or []):
                    yield path.name, "SequenceFeature", feature["feature_id"], position, entry


def build(con: duckdb.DuckDBPyConnection, directory: Path) -> None:
    view = SchemaView(str(SCHEMA))
    cols = columns(view)
    extra = {"source_file": "VARCHAR", "parent_class": "VARCHAR", "parent_id": "VARCHAR", "position": "INTEGER"}
    con.execute(
        "CREATE TABLE attribute_value ("
        + ", ".join(f'"{name}" {sqltype}' for name, sqltype in {**extra, **cols}.items())
        + ")"
    )
    names = list(extra) + list(cols)
    for source_file, parent_class, parent_id, position, entry in rows(directory):
        unknown = set(entry) - set(cols)
        if unknown:
            raise ValueError(f"{source_file}: slots not in Measurement: {sorted(unknown)}")
        # YAML reads some text values as numbers or dates; VARCHAR columns keep them as text.
        values = [str(v) if v is not None and cols[c] == "VARCHAR" else v for c, v in ((c, entry.get(c)) for c in cols)]
        con.execute(
            f"INSERT INTO attribute_value VALUES ({', '.join('?' for _ in names)})",
            [source_file, parent_class, parent_id, position, *values],
        )
    con.execute("CREATE TABLE sample AS SELECT * FROM (VALUES (NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR)) t(id, name, sample_category) WHERE false")
    for path in sorted(directory.glob("Sample-*.yaml")):
        data = yaml.safe_load(path.read_text())
        con.execute("INSERT INTO sample VALUES (?, ?, ?)", [data.get("id"), data.get("name"), data.get("sample_category")])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=":memory:")
    parser.add_argument("directory", nargs="?", default="tests/data/valid", type=Path)
    args = parser.parse_args()
    con = duckdb.connect(args.db)
    build(con, args.directory)
    queries = {
        "Rows by class and where they sit": """
            SELECT tbd_type_designator, coalesce(parent_class, '(own file)') AS parent_class, count(*) AS n_rows
            FROM attribute_value GROUP BY ALL ORDER BY ALL""",
        "The mixed sample: Attributes and Measurements in one list": """
            SELECT s.id, s.name, a.position, a.tbd_type_designator, a.key, a.attribute_cv_id, a.raw_value,
                   a.numeric_value, a.minimum_numeric_value, a.maximum_numeric_value, a.unit, a.value_cv_id, a.value_type
            FROM attribute_value a JOIN sample s ON a.parent_id = s.id
            WHERE a.parent_class = 'Sample' ORDER BY a.position""",
        "The GFF3 column 9 pair": """
            SELECT parent_id, position, tbd_type_designator, key, raw_value, numeric_value
            FROM attribute_value WHERE source_file LIKE 'SequenceFeature-%'""",
        "Adapted examples from bertron-schema issue 62": """
            SELECT source_file, tbd_type_designator, key, attribute_cv_id, raw_value, numeric_value,
                   value_cv_id, value_type, unit, unit_cv_id
            FROM attribute_value WHERE source_file LIKE '%-aj62-%' ORDER BY source_file""",
        "Columns that are never filled": """
            SELECT column_name FROM (UNPIVOT (SELECT count(COLUMNS(*)) FROM attribute_value) ON COLUMNS(*) INTO NAME column_name VALUE n)
            WHERE n = 0""",
    }
    for title, sql in queries.items():
        print(f"\n## {title}\n")
        con.sql(sql).show(max_width=400)


if __name__ == "__main__":
    main()
