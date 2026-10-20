# Cyclistic Bike-Share: Member vs. Casual Rider Behavior

This is the Google Data Analytics Professional Certificate capstone case study (Divvy/Cyclistic public trip data), extended beyond the standard capstone with a BigQuery layer and a full Python analysis. Worth stating that plainly: the case study itself is well known, and the differentiator here is the reconciliation and warehouse work built on top of it, not the prompt.

**Business question:** how do annual members and casual riders use the bike-share service differently, and what does that suggest for converting casual riders into members?

## Key finding (corrected 2026-09-16 — see below)

Members account for 91% of total rides. Casual riders take meaningfully longer trips on average — 38 minutes vs. 11 minutes for members (about 3.4x longer) — and ride more on weekends, consistent with leisure use, while members show clear commuting peaks around 8am and 5pm on weekdays.

## Pipeline

1. **`python/Cyclist_Analysis_Python.py`** — reconciles two quarterly Divvy exports with different schemas (2019: `trip_id`/`usertype`/`Subscriber`/`Customer`; 2020: `ride_id`/`member_casual`/`member`/`casual`), cleans and combines them, and produces the day-of-week, hour-of-day, and monthly comparison charts.
2. **`sql/cyclistic_bigquery.sql`** — the same cleaning and combination logic in BigQuery SQL, for reproducing the analysis at full-year scale in a cloud warehouse instead of local CSVs. (Not re-tested in this pass — no live BigQuery credentials in this environment. The SQL was reviewed for logic, not executed; it already applies the same 24-hour outlier cutoff described below, so it's a good reference for how the Python fix should behave.)

```bash
pip install -r requirements.txt
python "python/Cyclist_Analysis_Python.py"
```

`cyclistic_bigquery.sql` is written for Google BigQuery (free tier) — run it there directly against your own project.

## Tools

Python (pandas, matplotlib), Google BigQuery (SQL), Tableau Public.

## Dashboard

*(Add the public.tableau.com link for `Cyclist_Bike_Share_Viz`.)*

## Bugs found and fixed while testing this pipeline (2026-09-16)

1. **The reported "90 min vs 13 min" ride-length finding was outlier-contaminated.** The only filter on ride length was `> 0` — no upper bound. The dataset's max ride length is 10,632,022 seconds (~123 days), almost certainly a bike that was never docked rather than a real ride, and it was pulling casual riders' mean ride length up to ~90 minutes even though the median was ~23 minutes — a large mean/median gap that's a textbook outlier signal, not a real behavioral difference. The script's own "KEY FINDINGS" text was printing that inflated mean as if it were a clean insight. Added a 24-hour upper-bound filter (the same cutoff the BigQuery SQL in this project already used — the two layers had drifted apart) and reran 3 times: the corrected, honest finding is 38 min vs. 11 min (3.4x), not 90 vs. 13 (6.8x). Only 4,249 of ~792,000 rows (0.5%) were affected.
2. **A 2019 column was mislabeled.** `bikeid` (a numeric bike ID) was renamed directly to `rideable_type` (a 2020+ category like "docked_bike"), which conflates two different kinds of fields. It happened to be unused downstream so this was silent, but would have broken the moment anyone added a "rides by bike type" chart. Renamed to the accurate `bike_id`.

## Repo hygiene note

Three SQL file versions and two duplicate `outputs/` folders (one under `python/`, stale and superseded, now removed) were consolidated. The combined trip CSVs are 100MB+ and are excluded from git via `.gitignore` — they're fully regenerable by re-running the pipeline against the public Divvy data.
