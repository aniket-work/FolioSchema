"""Checks for the Cedar Hollow sample."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from folioschema.bind import BindError, load_archive
from folioschema.ontology import SchemaError, load_ontology
from folioschema.report import build_report

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def onto():
    return load_ontology(ROOT / "schema" / "archive.yaml")


@pytest.fixture
def archive(onto):
    return load_archive(ROOT / "data" / "archive.json", onto)


def test_sample_counts(onto, archive):
    report = build_report(onto, archive)
    assert report["items"] == 12
    assert report["needs_treatment"] == 6
    assert report["stable"] == 5
    assert report["neither"] == 1
    assert report["digitize_next"] == 7
    assert report["pull_risk"] == 2
    assert report["treatment_rate"] == pytest.approx(0.5)
    assert report["avg_condition"] == pytest.approx(34 / 12)
    assert report["scout_notes"] == 6
    assert report["worst_collection"] == "COL-TAPE"
    weak = {row["collection_id"]: row["needs_treatment"] for row in report["weak_collections"]}
    assert weak == {"COL-TAPE": 3, "COL-PHOTO": 2}


def test_it10_is_the_treatment_boundary(onto, archive):
    report = build_report(onto, archive)
    row = next(item for item in report["rows"] if item["item_id"] == "IT-10")
    assert row["condition_score"] == 2
    assert row["NeedsTreatment"] is True
    assert row["Stable"] is False
    assert row["DigitizeNext"] is True
    assert row["PullRisk"] is False


def test_it01_is_watched_and_still_digitized_next(onto, archive):
    report = build_report(onto, archive)
    row = next(item for item in report["rows"] if item["item_id"] == "IT-01")
    assert row["condition_score"] == 3
    assert row["NeedsTreatment"] is False
    assert row["Stable"] is False
    assert row["DigitizeNext"] is True
    assert row["PullRisk"] is False


def test_it07_is_the_healthy_undigitized_holdout(onto, archive):
    report = build_report(onto, archive)
    row = next(item for item in report["rows"] if item["item_id"] == "IT-07")
    assert row["digitized"] is False
    assert row["NeedsTreatment"] is False
    assert row["DigitizeNext"] is False
    assert row["PullRisk"] is False
    assert row["Stable"] is True


def test_metric_cannot_name_a_missing_property(tmp_path: Path):
    raw = yaml.safe_load((ROOT / "schema" / "archive.yaml").read_text(encoding="utf-8"))
    raw["metrics"].append(
        {
            "name": "InsuredValue",
            "grain": "Item",
            "definition": "A property this archive model does not have.",
            "rule": {"type": "at_least", "property": "appraisal_dollars", "minimum": 1},
        }
    )
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(SchemaError, match="appraisal_dollars"):
        load_ontology(path)


def test_unknown_collection_fails_bind(onto, tmp_path: Path):
    import json

    raw = json.loads((ROOT / "data" / "archive.json").read_text(encoding="utf-8"))
    raw["items"][0]["held_in"] = "COL-MISSING"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(BindError, match="COL-MISSING"):
        load_archive(path, onto)
