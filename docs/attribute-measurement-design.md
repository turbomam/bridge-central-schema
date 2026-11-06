# How Attribute and Measurement fit with core and SequenceFeature

This is a plan for a follow-up to https://github.com/doe-bridge/bridge-central-schema/pull/9, which can merge as it is. Nothing here asks for changes to that PR. The prototype is on branch `attribute-measurement-prototype` of https://github.com/turbomam/bridge-central-schema. Its first commit copies the inputs unchanged from four PRs, so the second commit shows the refactor as a diff. To keep the tables readable, the rest of this note calls each PR by its number:

- PR 16, https://github.com/doe-bridge/bridge-central-schema/pull/16: core.yaml, umbrella.yaml and the root schema, at d4bea60
- PR 9, https://github.com/doe-bridge/bridge-central-schema/pull/9: measurements.yaml, at 1c60157
- PR 12, https://github.com/doe-bridge/bridge-central-schema/pull/12: attributes.yaml, at 1671f40
- PR 6, https://github.com/doe-bridge/bridge-central-schema/pull/6: ber_feature_model.yaml, at 93d0b8e
- PR 5, https://github.com/doe-bridge/bridge-central-schema/pull/5: an earlier copy of ber_feature_model.yaml, at 15b0e06

Two aims guided it. An Attribute should be easy to subclass or compose with, and a Measurement should be about giving a value and a unit to some thing.

## The shape

- `Attribute` (in core.yaml) is one value given to a record. It holds what the value is of (`key`, free text, and `attribute_cv_id`, an optional identifier) and the value (`raw_value`, `numeric_value` as a double, `value_cv_id` for a term, and `value_type`). It has no unit and no provenance. It needs a key or an identifier, and a raw, numeric or term value.
- `Measurement` (in measurements.yaml) has `is_a: Attribute`. It adds `unit` (PR 9's UCUM code), `unit_cv_id`, `unit_basis`, a range (`minimum_numeric_value`, `maximum_numeric_value`) and `feature_of_interest`. PR 9's other slots come from five mixins: `MethodDetails`, `TimeDetails`, `StatisticDetails`, `ValueQualifiers` and `SourceDetails`.
- `tbd_type_designator` (in core.yaml) is a placeholder name for the type slot that https://github.com/doe-bridge/bridge-central-schema/issues/35 asks for. The real name is still undecided. Every Attribute and Measurement fills it with its class CURIE.
- `attributes` (in core.yaml) is one multivalued slot with range `Attribute`. `SequenceFeature` uses it for GFF3 column 9 pairs, raw text first. PR 16's `Sample` uses it for a list that mixes Attributes and Measurements, told apart by `tbd_type_designator`.
- Every class, slot and enum asserts its URI, with `bridge_central_schema` as the default prefix. tests/test_element_uris.py checks this.

`unit_cv_id` is new. PR 9 has no unit identifier slot. I added it because https://github.com/ber-data/bertron-schema/issues/62 records a unit as text plus an ontology id (`unit: meter`, `unit_cv_id: UO:0000008`).

The five mixins hold PR 9's slots without changing them. I used mixins rather than a separate context class for three reasons. A Measurement row keeps the same columns it has in PR 9, so data written for PR 9 stays one flat row. A separate class would need either nesting, which the style rules allow only in the feature model, or an id to link by, and most measurements have none. Any other class can take one mixin, such as `SourceDetails`, without the rest.

## Is a Measurement a kind of Attribute?

I think so, and the prototype uses `is_a`. An Attribute is a record of one value of one property, given to something. Every Measurement is such a record. What makes it a Measurement is what it carries: a unit, a range, what the value is about, and how and when the value was obtained. The class hierarchy then says what the records are, not how they are used. The same parent and child pair exists in nmdc-schema, where `QuantityValue` is a subclass of `AttributeValue` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L30). It also exists in BERtron (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L99) and in the KBase CDM (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L213).

The name Measurement claims more than the class holds. PR 9's `value_role` allows values that were set as a condition, interpreted or derived, so a Measurement need not come from an instrument. The class comments now say so.

The alternative gives the two classes no common parent. Both take their property and value slots from one mixin. It is in drafts/attribute-measurement/mixin-shape.yaml, with a mixed sample that validates and a counterexample that fails.

```yaml
# Chosen: is_a                          # Alternative: shared mixin
Attribute:                              PropertyValueSlots:
  slots: [tbd_type_designator, key,       mixin: true
    attribute_cv_id, raw_value, ...]      slots: [key, attribute_cv_id, raw_value, ...]
Measurement:                            Attribute:
  is_a: Attribute                         mixins: [PropertyValueSlots]
  mixins: [MethodDetails, ...]          Measurement:
  slots: [unit, feature_of_interest]      mixins: [PropertyValueSlots, MethodDetails, ...]
attributes:                             attributes:
  range: Attribute                        range: Any
                                          any_of: [{range: Attribute}, {range: Measurement}]
```

What each shape costs, checked with linkml 1.11.1 on 2026-11-06:

| | `is_a` | shared mixin |
|---|---|---|
| A list holding both | plain `range: Attribute` | needs `range: Any` with `any_of`, and an `Any` class |
| `SequenceFeature.attributes` | also accepts a Measurement, which validates | accepts only Attributes |
| Class rules (`any_of`, `exactly_one_of`) | not inherited: linkml-validate does not apply a parent's `any_of` to a subclass, so Measurement states its own | each class states its own anyway |
| Matches nmdc-schema, BERtron, KBase CDM | yes | no |

## Slot mapping from PR 9 and PR 12

| Slot today | From | Prototype slot | Defined on | Notes |
|---|---|---|---|---|
| `measurement_id` | PR 9 | `measurement_id` | Measurement | Likely removed, because it repeats `source_record_id`. Not moved into a mixin. |
| `observed_property` | PR 9 | `attribute_cv_id` | Attribute | Measurement keeps PR 9's `bridge_property:` pattern through `slot_usage`. `observed_property` is an alias. |
| `property_label` | PR 9 | `key` | Attribute | Measurement keeps PR 9's rule of exactly one of `attribute_cv_id` or `key`. |
| `feature_of_interest` | PR 9 | `feature_of_interest` | Measurement | Unchanged. |
| `raw_value` | PR 9 | `raw_value` | Attribute | Description merged with PR 12's `value`. |
| `numeric_value` | PR 9 | `numeric_value` | Attribute, from core | `double`, per https://github.com/doe-bridge/bridge-central-schema/issues/36 |
| `minimum_numeric_value` | PR 9 | `minimum_numeric_value` | Measurement; slot defined in core | `double` |
| `maximum_numeric_value` | PR 9 | `maximum_numeric_value` | Measurement; slot defined in core | `double` |
| `unit` | PR 9 | `unit` | Measurement | UCUM code, unchanged. |
| `unit_basis` | PR 9 | `unit_basis` | Measurement | Unchanged. |
| `coded_value` | PR 9 | `value_cv_id` | Attribute | `coded_value` is an alias. |
| `comparator` | PR 9 | `comparator` | `ValueQualifiers` mixin | Unchanged. |
| `statistic` | PR 9 | `statistic` | `StatisticDetails` mixin | Unchanged. |
| `standard_deviation` | PR 9 | `standard_deviation` | `StatisticDetails` mixin | Unchanged. |
| `sample_size` | PR 9 | `sample_size` | `StatisticDetails` mixin | Unchanged. |
| `value_role` | PR 9 | `value_role` | `ValueQualifiers` mixin | Unchanged. |
| `value_qualifier` | PR 9 | `value_qualifier` | `ValueQualifiers` mixin | Unchanged. |
| `missing_value_reason` | PR 9 | `missing_value_reason` | `ValueQualifiers` mixin | Unchanged. |
| `measurement_method` | PR 9 | `measurement_method` | `MethodDetails` mixin | Unchanged. Not renamed `method`, which `SequenceFeature` already uses. |
| `treatment` | PR 9 | `treatment` | `MethodDetails` mixin | Unchanged. |
| `instrument` | PR 9 | `instrument` | `MethodDetails` mixin | Unchanged. |
| `observed_time` | PR 9 | `observed_time` | `TimeDetails` mixin | Unchanged. |
| `observed_start_time` | PR 9 | `observed_start_time` | `TimeDetails` mixin | Unchanged. |
| `observed_end_time` | PR 9 | `observed_end_time` | `TimeDetails` mixin | Unchanged. |
| `source_system` | PR 9 | `source_system` | `SourceDetails` mixin | Pending: it may change from naming the source's schema to naming the source. |
| `source_record_id` | PR 9 | `source_record_id` | `SourceDetails` mixin | Unchanged. |
| `source_field` | PR 9 | `source_field` | `SourceDetails` mixin | Unchanged. |
| `quality_flag` | PR 9 | `quality_flag` | `ValueQualifiers` mixin | Unchanged. |
| `key` | PR 12 | `key` | Attribute | No longer required on its own; an Attribute needs `key` or `attribute_cv_id`. |
| `value` | PR 12 | `raw_value` | Attribute | Renamed to match PR 9. Recommended, not required. |
| `attribute_cv_id` | PR 12 | `attribute_cv_id` | Attribute | Unchanged. |
| `numeric_value` | PR 12 | `numeric_value` | Attribute, from core | Same slot as PR 9's. |
| none | new | `tbd_type_designator` | Attribute | Placeholder name. |
| none | new | `value_type` | Attribute | From https://github.com/ber-data/bertron-schema/issues/62 |
| none | new | `unit_cv_id` | Measurement | From https://github.com/ber-data/bertron-schema/issues/62 |
| `attributes` (PR 6) | PR 6 | `attributes` | core; used by SequenceFeature and Sample | The GFF3 mapping moves to `SequenceFeature`'s `slot_usage`. |

## Mapping to issue 62, NMDC, BERtron and the KBase CDM

The AJ column is the "simpler version" and the later flat field list in https://github.com/ber-data/bertron-schema/issues/62. NMDC links are to nmdc-schema at 270aefe, BERtron to bertron-schema at 4dcd838, and the KBase CDM to cdm-schema at c1a59b9.

| Prototype | Issue 62 (AJ) | NMDC AttributeValue family | BERtron | KBase CDM |
|---|---|---|---|---|
| `tbd_type_designator` | `type` names the kind of value, not the class | `type`, `designates_type: true` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L212) | none; `properties` is `any_of` TextValue or QuantityValue (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_schema.yaml#L113) | `type`, an enum of class names (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L99) |
| `key` | `attribute`, later `attribute_string` or `attribute_cv_label` | the slot that holds the value names it; `PropertyAssertion` has `has_attribute_label` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L295) | `attribute.label` (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L86) | `attribute_string` and `attribute_cv_label` (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L28) |
| `attribute_cv_id` | `attribute_cv_id` | `has_attribute_id` on `PropertyAssertion` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L306) | `attribute.id` | `attribute_cv_id` (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L21) |
| `raw_value` | `raw_value` | `has_raw_value` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L199) | `raw_value` (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L43) | `raw_value` |
| `numeric_value` (double) | `numeric_value` | `has_numeric_value`, `decimal` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L238) | `numeric_value`, `float` (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L23) | `numeric_value`, `float` (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L72) |
| `minimum_numeric_value`, `maximum_numeric_value` | listed as possible | `has_minimum_numeric_value`, `has_maximum_numeric_value` | same names | same names |
| `value_cv_id` | `value_cv_id` | `term` on `ControlledTermValue`, an `OntologyClass` with id and name (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L73); `has_value_term_id` on `PropertyAssertion` | `value_cv_id` on `TextValue` (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L68) | `value_cv_id` |
| none (term label) | `value_cv_label` | `term.name` | none | `value_cv_label` |
| `raw_value` (text value) | `value`, later `value_string` | `has_raw_value` on `TextValue` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L61) | `value` on `TextValue` | `text_value` |
| none (parsed date) | `datetime` | `has_raw_value` on `TimestampValue`; `has_datetime_value` on `PropertyAssertion` | `value` on `DateTimeValue` | `date_time` |
| `value_type` | `type`: float, integer, iso_datetime, cv_term, text, json | the class: QuantityValue, TextValue, TimestampValue, ControlledTermValue | the class | the class, named in `type` |
| `unit` (UCUM code) | `unit` (text), later `unit_string` or `unit_cv_label` | `has_unit`, an enum on `QuantityValue` (https://github.com/microbiomedata/nmdc-schema/blob/270aefeda91443c6cbb6e8bfd340f6ec09e74b8c/src/schema/attribute_values.yaml#L30) | `unit` (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L49) | `unit_string`, `unit_cv_label` |
| `unit_cv_id` | `unit_cv_id` | none | `unit_cv_id` (https://github.com/ber-data/bertron-schema/blob/4dcd83800df2320ac7a7129df718f8f235775271/src/schema/linkml/bertron_types.yaml#L60) | `unit_cv_id` (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L103) |
| `feature_of_interest` (Measurement only) | none | none; the value is nested in its record | none; nested in its entity | `entity_id`, required on every value (https://github.com/kbase/cdm-schema/blob/c1a59b9607abc85affe3d17f0239ef4e2b819f61/src/linkml/cdm_attr_value.yaml#L161) |

## What each PR would change

PR 9 (https://github.com/doe-bridge/bridge-central-schema/pull/9) needs no change and can merge as it is. Every Measurement change below could go in one follow-up PR after PR 16 merges, because it depends on core.yaml:

- Measurement gets `is_a: Attribute` and the five mixins.
- `observed_property` becomes `attribute_cv_id`, `property_label` becomes `key`, and `coded_value` becomes `value_cv_id`, with the old names kept as aliases.
- `raw_value`, `numeric_value` and the range slots come from core.
- `unit_cv_id` and `value_type` are added.
- Every example gets the type slot. The prototype changes the 27 valid, 12 invalid and 4 problem Measurement examples this way and keeps their data otherwise.

PR 12 (https://github.com/doe-bridge/bridge-central-schema/pull/12) could be closed in favor of `Attribute` in core.yaml, or retargeted to add it there. Either way, `value` becomes `raw_value`, `key` is no longer required on its own, the `notes` become `comments`, and `numeric_value` comes from core.

PR 16 (https://github.com/doe-bridge/bridge-central-schema/pull/16) would add `Attribute`, its slots, `ValueTypeEnum`, the type slot and the `attributes` slot to core.yaml, and `attributes` to `Sample`. The prototype also adds the 20 missing URIs in umbrella.yaml.

PR 5 and PR 6 (https://github.com/doe-bridge/bridge-central-schema/pull/5, https://github.com/doe-bridge/bridge-central-schema/pull/6) would import `core` instead of `attributes`, drop their own `attributes` slot, and keep its GFF3 mapping in `SequenceFeature`'s `slot_usage`. Their examples would add the type slot to every pair and rename `value` to `raw_value`: 230 pairs across Dataset-001 to Dataset-004 at 93d0b8e.

## Descriptions that claim more than they hold

Each class in the prototype now says what it is, what it inherits and adds, and what it is for and not for. These current descriptions don't yet do that. I haven't edited them; the suggestions are for each PR's owner.

| Element | File and line | Problem | Suggested wording |
|---|---|---|---|
| `NamedThing` | core.yaml:35 at d4bea60 (PR 16) | Doesn't say what it adds or what does not inherit from it | "Base class for records that have their own id. Adds id, name, description and external_identifiers. Attribute and Measurement do not inherit from it." |
| `id` | core.yaml:47 at d4bea60 (PR 16) | "unique" is not checked across tables | "The record's identifier, as a CURIE. Unique within its table; uniqueness across tables is checked after loading." |
| `Measurement` | measurements.yaml:51 at 1c60157 (PR 9) | The name suggests a reading from an instrument; values can be settings, interpretations or derived; the description narrates the hackathon | "One value of one property of one thing, as a source reports it. The value can be measured, set, interpreted or derived (value_role). Not an observation event and not a time series." |
| `observed_property` | measurements.yaml:158 at 1c60157 (PR 9) | "was measured" is wrong for settings and interpreted values | "The property the value is of, as a BRIDGE property identifier (bridge_property:)." |
| `source_system` | measurements.yaml:335 at 1c60157 (PR 9) | The name says system; the value is a registry entry for the source's schema | Pending the decision on its meaning. If it stays: "The source's schema, as its BER lakehouse registry entry." |
| `Attribute` | attributes.yaml:23 at 1671f40 (PR 12) | Doesn't say it has no unit or provenance, or what it is not for; the rest is in `notes` | "One named value given to a record, as the source wrote it. Inherits from nothing. Not for values with a unit." |
| attributes module | attributes.yaml:5 at 1671f40 (PR 12) | "String-valued" while the class has `numeric_value` | "Attributes: a source's name and text value, with an optional identifier for the name and an optional number." |
| `Dataset` | ber_feature_model.yaml:50 at 93d0b8e (PR 6); line 42 at 15b0e06 (PR 5) | "every Contig and SequenceFeature" claims completeness | "A document holding Contigs and SequenceFeatures harmonized from one or more workflow executions." |
| `SequenceFeature` | ber_feature_model.yaml:100 at 93d0b8e (PR 6); line 89 at 15b0e06 (PR 5) | Holds evidence hits in protein coordinates and joined locations, which the description doesn't cover | "A sequence interval with its annotation: a gene or CDS call, or an evidence hit on one, located on a contig or on a protein." |
| `attributes` | ber_feature_model.yaml:597 at 93d0b8e (PR 6); line 519 at 15b0e06 (PR 5) | "evidence" claims more than key and text pairs | "GFF3 column 9 tags that have no slot of their own, as ordered key and value pairs." |

## Test and load results

On 2026-11-06 with linkml 1.11.1, `just test` passed (226 pytest tests, plus generation of every project artifact). Run file by file with linkml-validate, all 63 valid examples passed and all 29 invalid examples failed. tests/test_element_uris.py passed for 134 classes, slots and enums. `just lint` reports one warning, the `example` prefix that PR 9 declares.

`just attribute-duckdb` loads every Attribute and Measurement into one DuckDB table, whether it is a file of its own or an entry in a list:

| tbd_type_designator | parent_class | n_rows |
|---|---|---|
| bridge_central_schema:Attribute | (own file) | 8 |
| bridge_central_schema:Attribute | Sample | 3 |
| bridge_central_schema:Attribute | SequenceFeature | 231 |
| bridge_central_schema:Measurement | (own file) | 28 |
| bridge_central_schema:Measurement | Sample | 2 |

## Open questions

1. What is the type slot's name? https://github.com/doe-bridge/bridge-central-schema/issues/35 lists `type` with the GFF3 slot renamed, `record_type`, or `type` everywhere except `SequenceFeature`. The prototype uses `tbd_type_designator` until that is decided.
2. Should every GFF3 pair carry the type slot? It is required now, so each of the 230 pairs in the feature model examples carries the same value.
3. Should a sample's Attributes and Measurements be nested in the sample, as the prototype does, or be rows of their own table that point at the sample? The style rules allow nesting only in the feature model. Rows of their own would need Attribute to say what it is about, as the KBase CDM's required `entity_id` does; today only Measurement has `feature_of_interest`.
4. Should a Measurement's `attribute_cv_id` allow identifiers other than `bridge_property:`? PR 9's pattern rejects `MIXS:0000117`, so the adapted total phosphorus example from issue 62 names its property only in `key`.
5. Should a Measurement allow both `key` and `attribute_cv_id`? PR 9 allows exactly one. Issue 62 asks for an id and a label together, and Attribute allows both.
6. Do we need a slot for a parsed date? Issue 62's `datetime`, NMDC's `has_datetime_value` and the KBase CDM's `date_time` all have one. The prototype keeps a date only in `raw_value`.
7. Do we need a term label (`value_cv_label`), and a slot naming the enumeration a term comes from (issue 62's `BearSizeEnum`)?
8. Should `value_type` say `float`, the word issue 62 uses, when the number is stored as a double?
9. Is it a problem that `SequenceFeature.attributes` also accepts Measurements? The mixin shape avoids that.
10. `raw_value`: PR 9 says it is never edited, and PR 12 decodes GFF3 escapes. The prototype decodes escapes and changes nothing else. Is that right for both?
11. If units become rows of their own table, does `unit_cv_id` move to that table?
