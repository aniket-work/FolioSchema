# FolioSchema

A personal experiment that keeps one definition for four preservation calls on a fictional town archive.

**How I Defined Treatment, Stability, and Digitization in One Model**

The model lives in `schema/archive.yaml`. The rows live in `data/archive.json`. Python loads the model, refuses a metric that names a property the item does not have, binds the rows, and prints one brief. The CLI and the small HTTP API both call `build_report`. They do not each invent a cutoff.

![FolioSchema cover](https://raw.githubusercontent.com/aniket-work/FolioSchema/main/images/title-animation.gif)

## What the sample says

Cedar Hollow is invented. Twelve objects. Three collections: town council minutes, flood photographs, oral history tapes. The fact grain is `Item`. Dimensions are `Collection`, `Location`, and `Format`.

| Call | Rule in this experiment |
| --- | --- |
| NeedsTreatment | `condition_score` is 2 or lower |
| Stable | `condition_score` is 4 or higher |
| DigitizeNext | not digitized, and score is 3 or lower or year is 1940 or earlier |
| PullRisk | pulled at least 5 times and score is 3 or lower |

On this sample the brief prints:

1. 12 items, 6 need treatment, 5 are stable, 1 is neither. Treatment rate 50.0 percent.
2. 7 items are `DigitizeNext`. 2 items are `PullRisk`. Average condition score 2.83. Six notes contain a scout word.
3. Collections at or above a 50 percent treatment rate: `COL-TAPE` (3/4) and `COL-PHOTO` (2/4).
4. The collection I would open first is `COL-TAPE`.

`IT-10` sits on the treatment boundary: score exactly 2, so it counts. `IT-01` is score 3, so it is not queued for treatment, and it is still `DigitizeNext` because it has no surrogate. `IT-07` is undigitized, score 5, made in 1978, pulled six times, and it matches none of the risk calls. That split is the point of separate metrics.

The 50 percent line is a reporting cutoff in `report.py`. It is not a class in the YAML. The cutoffs (score 2, score 4, score 3, five pulls, year 1940) are constants I picked so the sample would show both sides of each rule. They are not a conservation policy.

## Layout

```
FolioSchema/
  main.py                 CLI brief
  api.py                  FastAPI wrapper around the same report
  schema/archive.yaml     classes, relationships, metrics
  data/archive.json       fictional rows
  folioschema/ontology.py load and validate the model
  folioschema/bind.py     keys, ranges, relationship targets
  folioschema/metrics.py  score declared rules only
  folioschema/report.py   one brief
  folioschema/chart.py    treatment rate by collection
  static/dashboard.html   reads GET /api/brief
  tests/test_schema.py
  images/
```

![Architecture](https://raw.githubusercontent.com/aniket-work/FolioSchema/main/images/architecture_diagram.png)

## Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python main.py --chart images/treatment-chart.png
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. uvicorn api:app --port 8077
```

`GET /api/brief` returns the same counts as the terminal table, without the row list.

![Treatment rate](https://raw.githubusercontent.com/aniket-work/FolioSchema/main/images/treatment-chart.png)

## What this does not do

The YAML does not query a catalog. It does not move a box. A passing `load_ontology` means the metric names real properties and the relationships point at classes that exist. It does not mean a conservator would agree with score 2 as the queue line. Scout words (`foxing`, `brittle`, `curl`, `silvering`, `sticky`, `shed`) are a note scan in `ontology.py`. They are not a fifth metric.

![Sequence](https://raw.githubusercontent.com/aniket-work/FolioSchema/main/images/sequence_diagram.png)
