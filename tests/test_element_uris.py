"""Every class, slot and enum in the schema asserts its URI.

The rule is https://github.com/doe-bridge/bridge-central-schema/issues/35. Elements
imported from linkml:types are skipped.
"""

from pathlib import Path

import pytest
from linkml_runtime import SchemaView

SCHEMA = Path(__file__).parents[1] / "src" / "ber_central_schema" / "schema" / "ber_central_schema.yaml"
VIEW = SchemaView(str(SCHEMA))


def own(elements):
    return sorted(
        name for name, element in elements.items() if not (element.from_schema or "").startswith("https://w3id.org/linkml/")
    )


@pytest.mark.parametrize("name", own(VIEW.all_classes()))
def test_class_asserts_class_uri(name):
    assert VIEW.get_class(name).class_uri, f"class {name} has no class_uri"


@pytest.mark.parametrize("name", own(VIEW.all_slots()))
def test_slot_asserts_slot_uri(name):
    assert VIEW.get_slot(name).slot_uri, f"slot {name} has no slot_uri"


@pytest.mark.parametrize("name", own(VIEW.all_enums()))
def test_enum_asserts_enum_uri(name):
    assert VIEW.get_enum(name).enum_uri, f"enum {name} has no enum_uri"
