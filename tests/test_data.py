"""Data test."""

import os
import glob
import pytest
from pathlib import Path

import ber_central_schema.datamodel.ber_central_schema
from linkml_runtime.loaders import yaml_loader
from linkml.validator import validate
from linkml_runtime import SchemaView
import yaml

SCHEMA = Path(__file__).parents[1] / "src" / "ber_central_schema" / "schema" / "ber_central_schema.yaml"
DATA_DIR_VALID = Path(__file__).parent / "data" / "valid"
DATA_DIR_INVALID = Path(__file__).parent / "data" / "invalid"

VALID_EXAMPLE_FILES = glob.glob(os.path.join(DATA_DIR_VALID, "*.yaml"))
INVALID_EXAMPLE_FILES = glob.glob(os.path.join(DATA_DIR_INVALID, "*.yaml"))


@pytest.mark.parametrize("filepath", VALID_EXAMPLE_FILES)
def test_valid_data_files(filepath):
    """Test loading of all valid data files."""
    target_class_name = Path(filepath).stem.split("-")[0]
    tgt_class = getattr(
        ber_central_schema.datamodel.ber_central_schema,
        target_class_name,
    )
    obj = yaml_loader.load(filepath, target_class=tgt_class)
    assert obj


@pytest.mark.parametrize("filepath", INVALID_EXAMPLE_FILES)
def test_invalid_data_files(filepath):
    """Every counterexample must fail validation against its class."""
    target_class_name = Path(filepath).stem.split("-")[0]
    instance = yaml.safe_load(Path(filepath).read_text())
    # Load through SchemaView so imports resolve beside the schema, not the working directory.
    schema = SchemaView(str(SCHEMA)).materialize_derived_schema()
    report = validate(instance, schema, target_class_name)
    assert report.results, f"{filepath} validated, but it is a counterexample"
