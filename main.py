#!/usr/bin/env python3
"""Print the Cedar Hollow preservation brief."""

from __future__ import annotations

import argparse
from pathlib import Path

from folioschema.bind import load_archive
from folioschema.chart import write_chart
from folioschema.ontology import load_ontology
from folioschema.report import build_report

ROOT = Path(__file__).resolve().parent


def _yn(flag: bool) -> str:
    return "yes" if flag else "no"


def main() -> None:
    parser = argparse.ArgumentParser(description="FolioSchema preservation brief")
    parser.add_argument(
        "--chart",
        default="",
        help="Optional path for the treatment-rate chart",
    )
    args = parser.parse_args()
    onto = load_ontology(ROOT / "schema" / "archive.yaml")
    archive = load_archive(ROOT / "data" / "archive.json", onto)
    report = build_report(onto, archive)

    print(f"ontology {report['ontology']} v{report['version']}")
    print("fact grain: Item")
    print("metric NeedsTreatment on Item: condition_score <= 2")
    print(
        f"{'ID':<6} {'COLLECTION':<12} {'SCORE':>5} {'TREAT':>5} "
        f"{'STABLE':>6} {'DIGIT':>5} {'PULL':>5} NOTE"
    )
    for row in report["rows"]:
        note = row["note"] or "-"
        print(
            f"{row['item_id']:<6} {row['held_in']:<12} {row['condition_score']:>5} "
            f"{_yn(row['NeedsTreatment']):>5} {_yn(row['Stable']):>6} "
            f"{_yn(row['DigitizeNext']):>5} {_yn(row['PullRisk']):>5} {note}"
        )
    rate = report["treatment_rate"] * 100
    print(
        f"items={report['items']} needs_treatment={report['needs_treatment']} "
        f"stable={report['stable']} neither={report['neither']} "
        f"treatment_rate={rate:.1f}%"
    )
    print(
        f"digitize_next={report['digitize_next']} pull_risk={report['pull_risk']} "
        f"avg_condition={report['avg_condition']:.2f} scout_notes={report['scout_notes']}"
    )
    weak = ", ".join(
        f"{row['collection_id']} ({row['needs_treatment']}/{row['items']})"
        for row in report["weak_collections"]
    )
    print(f"collections at or above 50% NeedsTreatment: {weak}")
    print(f"open first: {report['worst_collection']}")
    if args.chart:
        chart_path = Path(args.chart)
        write_chart(report, chart_path)
        print(f"chart: {chart_path}")


if __name__ == "__main__":
    main()
