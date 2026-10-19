"""Score item rows with the rules declared on the ontology."""

from __future__ import annotations

from typing import Any

from folioschema.ontology import MetricDef, Ontology, SchemaError


def _score_metric(metric: MetricDef, row: dict[str, Any]) -> bool:
    rule = metric.rule
    kind = rule["type"]
    if kind == "at_most":
        return int(row[rule["property"]]) <= int(rule["maximum"])
    if kind == "at_least":
        return int(row[rule["property"]]) >= int(rule["minimum"])
    if kind == "undigitized_and":
        if row[rule["property_flag"]] is not False:
            return False
        weak_score = int(row[rule["score"]]) <= int(rule["score_maximum"])
        early_year = int(row[rule["year"]]) <= int(rule["year_maximum"])
        return weak_score or early_year
    if kind == "both_bounds":
        low_ok = int(row[rule["low_property"]]) <= int(rule["low_maximum"])
        high_ok = int(row[rule["high_property"]]) >= int(rule["high_minimum"])
        return low_ok and high_ok
    raise SchemaError(f"cannot score rule type {kind}")


def score_items(onto: Ontology, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in items:
        flags = {metric.name: _score_metric(metric, row) for metric in onto.metrics}
        scored.append({**row, **flags})
    return scored


def collection_treatment_rate(
    scored: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[str, list[bool]] = {}
    for row in scored:
        buckets.setdefault(row["held_in"], []).append(bool(row["NeedsTreatment"]))
    rates: list[dict[str, Any]] = []
    for collection_id, flags in buckets.items():
        hits = sum(1 for flag in flags if flag)
        rate = hits / len(flags) if flags else 0.0
        rates.append(
            {
                "collection_id": collection_id,
                "items": len(flags),
                "needs_treatment": hits,
                "rate": rate,
            }
        )
    rates.sort(key=lambda item: (-item["rate"], item["collection_id"]))
    return rates
