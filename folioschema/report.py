"""One brief for the CLI and the API."""

from __future__ import annotations

from typing import Any

from folioschema.metrics import collection_treatment_rate, score_items
from folioschema.ontology import SCOUT_WORDS, Ontology

TREATMENT_CUTOFF = 0.50


def _note_hits(note: str) -> list[str]:
    lowered = note.lower()
    return [word for word in SCOUT_WORDS if word in lowered]


def build_report(onto: Ontology, archive: dict[str, Any]) -> dict[str, Any]:
    scored = score_items(onto, archive["items"])
    rates = collection_treatment_rate(scored)
    weak = [row for row in rates if row["rate"] >= TREATMENT_CUTOFF]
    treatment = [row for row in scored if row["NeedsTreatment"]]
    stable = [row for row in scored if row["Stable"]]
    digitize = [row for row in scored if row["DigitizeNext"]]
    pull = [row for row in scored if row["PullRisk"]]
    notes = []
    for row in scored:
        hits = _note_hits(row.get("note") or "")
        if hits:
            notes.append({"item_id": row["item_id"], "words": hits})
    count = len(scored)
    avg_score = sum(row["condition_score"] for row in scored) / count if count else 0.0
    return {
        "ontology": onto.name,
        "version": onto.version,
        "items": count,
        "needs_treatment": len(treatment),
        "stable": len(stable),
        "neither": count - len(treatment) - len(stable),
        "digitize_next": len(digitize),
        "pull_risk": len(pull),
        "treatment_rate": (len(treatment) / count) if count else 0.0,
        "avg_condition": avg_score,
        "scout_notes": len(notes),
        "rows": scored,
        "by_collection": rates,
        "weak_collections": weak,
        "worst_collection": weak[0]["collection_id"] if weak else None,
        "treatment_ids": [row["item_id"] for row in treatment],
        "digitize_ids": [row["item_id"] for row in digitize],
        "pull_ids": [row["item_id"] for row in pull],
        "note_hits": notes,
        "cutoff": TREATMENT_CUTOFF,
    }
