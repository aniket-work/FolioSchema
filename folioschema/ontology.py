"""Load and check the archive semantic model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SCOUT_WORDS = ("foxing", "brittle", "curl", "silvering", "sticky", "shed")


class SchemaError(ValueError):
    """The YAML model is internally inconsistent."""


@dataclass
class PropertyDef:
    name: str
    type_name: str
    definition: str


@dataclass
class RelationshipDef:
    name: str
    target: str
    cardinality: str


@dataclass
class ClassDef:
    name: str
    kind: str
    key: str
    definition: str
    properties: list[PropertyDef] = field(default_factory=list)
    relationships: list[RelationshipDef] = field(default_factory=list)

    def property_names(self) -> set[str]:
        return {prop.name for prop in self.properties}


@dataclass
class MetricDef:
    name: str
    grain: str
    definition: str
    rule: dict[str, Any]


@dataclass
class Ontology:
    name: str
    version: str
    description: str
    classes: dict[str, ClassDef]
    metrics: list[MetricDef]
    constraints: list[dict[str, str]]

    def fact(self) -> ClassDef:
        facts = [cls for cls in self.classes.values() if cls.kind == "fact"]
        if len(facts) != 1:
            raise SchemaError(f"expected one fact class, found {len(facts)}")
        return facts[0]

    def metric(self, name: str) -> MetricDef:
        for item in self.metrics:
            if item.name == name:
                return item
        raise SchemaError(f"unknown metric {name}")


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise SchemaError(f"{where} is missing '{key}'")
    return mapping[key]


def _check_rule(metric: MetricDef, grain: ClassDef) -> None:
    rule = metric.rule
    kind = rule.get("type")
    names = grain.property_names()

    def need(prop_key: str) -> None:
        prop = rule.get(prop_key)
        if not isinstance(prop, str) or prop not in names:
            raise SchemaError(
                f"metric {metric.name} on {grain.name} names unknown property {prop!r}"
            )

    if kind == "at_most":
        need("property")
        if not isinstance(rule.get("maximum"), int):
            raise SchemaError(f"metric {metric.name} needs an integer maximum")
    elif kind == "at_least":
        need("property")
        if not isinstance(rule.get("minimum"), int):
            raise SchemaError(f"metric {metric.name} needs an integer minimum")
    elif kind == "undigitized_and":
        need("property_flag")
        need("score")
        need("year")
        if not isinstance(rule.get("score_maximum"), int):
            raise SchemaError(f"metric {metric.name} needs an integer score_maximum")
        if not isinstance(rule.get("year_maximum"), int):
            raise SchemaError(f"metric {metric.name} needs an integer year_maximum")
    elif kind == "both_bounds":
        need("low_property")
        need("high_property")
        if not isinstance(rule.get("low_maximum"), int):
            raise SchemaError(f"metric {metric.name} needs an integer low_maximum")
        if not isinstance(rule.get("high_minimum"), int):
            raise SchemaError(f"metric {metric.name} needs an integer high_minimum")
    else:
        raise SchemaError(f"metric {metric.name} has unknown rule type {kind!r}")


def validate_ontology(onto: Ontology) -> None:
    if not onto.classes:
        raise SchemaError("ontology has no classes")
    onto.fact()
    seen_metrics: set[str] = set()
    for metric in onto.metrics:
        if metric.name in seen_metrics:
            raise SchemaError(f"duplicate metric {metric.name}")
        seen_metrics.add(metric.name)
        if metric.grain not in onto.classes:
            raise SchemaError(f"metric {metric.name} grain {metric.grain} is not a class")
        _check_rule(metric, onto.classes[metric.grain])
    for cls in onto.classes.values():
        for rel in cls.relationships:
            if rel.target not in onto.classes:
                raise SchemaError(
                    f"{cls.name}.{rel.name} points at missing class {rel.target}"
                )
            if rel.cardinality != "many_to_one":
                raise SchemaError(
                    f"{cls.name}.{rel.name} cardinality {rel.cardinality} is not supported"
                )


def load_ontology(path: Path) -> Ontology:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SchemaError("ontology root must be a mapping")
    classes: dict[str, ClassDef] = {}
    for block in _require(raw, "classes", "ontology"):
        name = _require(block, "name", "class")
        if name in classes:
            raise SchemaError(f"duplicate class {name}")
        props = [
            PropertyDef(
                name=_require(prop, "name", f"{name} property"),
                type_name=_require(prop, "type", f"{name}.{prop.get('name', '?')}"),
                definition=_require(prop, "definition", f"{name} property"),
            )
            for prop in block.get("properties", [])
        ]
        rels = [
            RelationshipDef(
                name=_require(rel, "name", f"{name} relationship"),
                target=_require(rel, "target", f"{name} relationship"),
                cardinality=_require(rel, "cardinality", f"{name} relationship"),
            )
            for rel in block.get("relationships", [])
        ]
        classes[name] = ClassDef(
            name=name,
            kind=_require(block, "kind", name),
            key=_require(block, "key", name),
            definition=_require(block, "definition", name),
            properties=props,
            relationships=rels,
        )
    metrics = [
        MetricDef(
            name=_require(block, "name", "metric"),
            grain=_require(block, "grain", "metric"),
            definition=_require(block, "definition", "metric"),
            rule=_require(block, "rule", f"metric {block.get('name', '?')}"),
        )
        for block in _require(raw, "metrics", "ontology")
    ]
    onto = Ontology(
        name=_require(raw, "name", "ontology"),
        version=str(_require(raw, "version", "ontology")),
        description=_require(raw, "description", "ontology"),
        classes=classes,
        metrics=metrics,
        constraints=list(raw.get("constraints", [])),
    )
    validate_ontology(onto)
    return onto
