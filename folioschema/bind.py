"""Bind sample rows onto the classes named in the ontology."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from folioschema.ontology import Ontology, SchemaError


class BindError(ValueError):
    """A row does not match the model."""


def _index(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for row in rows:
        ident = row.get(key)
        if not isinstance(ident, str) or not ident:
            raise BindError(f"{label} row is missing {key}")
        if ident in found:
            raise BindError(f"duplicate {label} id {ident}")
        found[ident] = row
    return found


def _check_item(row: dict[str, Any]) -> None:
    score = row.get("condition_score")
    if not isinstance(score, int) or not 1 <= score <= 5:
        raise BindError(f"{row.get('item_id')} condition_score must be an integer from 1 to 5")
    year = row.get("year_created")
    if not isinstance(year, int) or not 1800 <= year <= 2020:
        raise BindError(f"{row.get('item_id')} year_created must be from 1800 through 2020")
    pulls = row.get("handling_count")
    if not isinstance(pulls, int) or pulls < 0:
        raise BindError(f"{row.get('item_id')} handling_count must be zero or greater")
    if not isinstance(row.get("digitized"), bool):
        raise BindError(f"{row.get('item_id')} digitized must be true or false")
    if not isinstance(row.get("note", ""), str):
        raise BindError(f"{row.get('item_id')} note must be a string")


def load_archive(path: Path, onto: Ontology) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    collections = _index(raw["collections"], "collection_id", "collection")
    locations = _index(raw["locations"], "location_id", "location")
    formats = _index(raw["formats"], "format_id", "format")
    items = _index(raw["items"], onto.fact().key, "item")

    item_cls = onto.fact()
    rel_targets = {rel.name: rel.target for rel in item_cls.relationships}
    expected = {
        "held_in": collections,
        "stored_at": locations,
        "recorded_as": formats,
    }
    if set(rel_targets) != set(expected):
        raise SchemaError(
            "item relationships must be held_in, stored_at, and recorded_as"
        )

    bound: list[dict[str, Any]] = []
    for item_id, row in items.items():
        _check_item(row)
        for rel_name, table in expected.items():
            target_id = row.get(rel_name)
            if target_id not in table:
                raise BindError(f"{item_id} {rel_name} {target_id!r} is not in the sample")
        bound.append(row)

    return {
        "collections": collections,
        "locations": locations,
        "formats": formats,
        "items": bound,
    }
