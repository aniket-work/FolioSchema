"""Bar chart of treatment rate by collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from folioschema.report import TREATMENT_CUTOFF


def write_chart(report: dict[str, Any], path: Path) -> None:
    rows = report["by_collection"]
    labels = [row["collection_id"].replace("COL-", "") for row in rows]
    rates = [row["rate"] * 100 for row in rows]
    colors = ["#d64545" if row["rate"] >= TREATMENT_CUTOFF else "#2f9e6b" for row in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=140)
    ax.bar(labels, rates, color=colors, width=0.62)
    ax.axhline(TREATMENT_CUTOFF * 100, color="#1f2a36", linestyle="--", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_ylabel("NeedsTreatment rate (%)")
    ax.set_title("Cedar Hollow sample — treatment rate by collection")
    for index, rate in enumerate(rates):
        ax.text(index, rate + 2, f"{rate:.0f}%", ha="center", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
