"""Same brief as the CLI, over HTTP."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from folioschema.bind import load_archive
from folioschema.ontology import load_ontology
from folioschema.report import build_report

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="FolioSchema")


def _report() -> dict:
    onto = load_ontology(ROOT / "schema" / "archive.yaml")
    archive = load_archive(ROOT / "data" / "archive.json", onto)
    report = build_report(onto, archive)
    report.pop("rows")
    return report


@app.get("/api/brief")
def brief() -> dict:
    return _report()


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(ROOT / "static" / "dashboard.html")
