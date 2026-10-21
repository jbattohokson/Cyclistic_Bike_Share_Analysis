# Cyclistic Bike-Share: Member vs. Casual Rider Behavior

The Google Data Analytics Professional Certificate capstone (Divvy/Cyclistic public trip data), extended with a BigQuery layer, a reconciliation of two incompatible export schemas, and tests. The case study itself is well known; the differentiator here is the cleaning and verification work, not the prompt.

## The problem

Cyclistic's finance team has found that annual members are more profitable than casual riders. Marketing wants to convert casual riders into members, and needs to know **how the two groups use the bikes differently** so the offer, timing and message fit how casual riders actually ride.

## What I did

1. **Reconciled two schemas.** Q1 2019 (`trip_id` / `usertype` = `Subscriber`/`Customer`) and Q1 2020 (`ride_id` / `member_casual` = `member`/`casual`) were mapped to one schema and stacked: 791,956 rows.
2. **Cleaned with explicit, counted rules.** Every dropped row is counted against the first rule it fails, and the script asserts that kept + dropped = input:

   | Rule | Rows dropped |
   |---|---:|
   | HQ QR station (Divvy's internal test rides) | 3,767 |
   | Ride longer than 24 hours (bike never docked) | 482 |
   | Zero/negative length, unknown rider type, unparseable timestamp | 0 |
   | **Kept** | **787,707** |

3. **Compared the groups** by ride length (mean *and* median), day of week, hour of day, month and start station. All five charts and three summary CSVs are in `outputs/`.

## Findings

Every number below is computed by `compute_findings()` and printed by the script, so the write-up can't drift from the data.

1. **Members take 91% of rides, but casual riders ride much longer.** Median 23 min vs 8.5 min (**2.7x**); mean 38 min vs 11 min (3.4x). The median is the fairer comparison: ride length is right-skewed, and the mean overstates the gap.
2. **Casual riders are weekend riders; members are commuters.** 47% of casual rides fall on Saturday or Sunday, and casual riders ride 2.2x as much per weekend day as per weekday. Members do the opposite: 17% of rides on weekends, about half as many per weekend day.
3. **Members show a commute signature.** On weekdays they peak at 8:00 and 17:00. Casual riders peak mid-afternoon (16:00–17:00) with no morning rush.
4. **Casual demand is more seasonal.** From January to March, casual rides grow 3.3x (12,312 → 40,392) while member rides grow 1.13x (234,683 → 265,225).

## Recommendations

1. **A weekend or leisure membership tier**, priced between per-ride rates and the annual plan, to fit how casual riders already ride and give them a path up to an annual membership.
2. **Market at the top casual start stations** (chart 5), on weekend afternoons, timed to ride completion.
3. **Show the savings.** Casual riders' rides are longer, so per-ride pricing costs them more; a cost comparison is the most direct pitch.
4. **Start campaigns in March**, when casual ridership is climbing, rather than waiting for summer.

## Limitations

- Q1 only (January–March). The seasonal finding covers the end of winter, not summer peaks.
- No rider IDs, so there is no way to measure how often an individual casual rider rides, their lifetime value, or conversion. The savings pitch needs per-rider data or a cohort estimate.
- The recommendations are hypotheses to A/B test against a holdout, not measured effects.

## Run it

```bash
pip install -r requirements.txt
python python/Cyclist_Analysis_Python.py   # reads the CSVs straight from data/*.zip, writes outputs/
python -m pytest tests/                    # edge-case tests for cleaning and findings
```

`sql/cyclistic_bigquery.sql` is the same pipeline in BigQuery SQL, for running at full-year scale in a cloud warehouse. Run it in your own BigQuery project (it references `big-query-486123.Cyclist_Data`; swap in your project and dataset).

## Tools

Python (pandas, matplotlib), Google BigQuery (SQL), Tableau Public, pytest.

## Dashboard

Tableau PDFs are in `tableau/`. *(Public Tableau link still to be added.)*

## Audit log

**2026-10-21 audit and rebuild**
- **The SQL and Python had drifted.** The BigQuery version never excluded HQ QR test rides (183 survived), and `TIMESTAMP_DIFF(..., MINUTE)` truncates, so every ride under 60 seconds became 0 and was dropped (3,908 rides the Python keeps). It now uses seconds and the same HQ QR + 24-hour rules. The same logic run in DuckDB against the CSVs gives 787,707 rows, matching Python. The duration buckets were rewritten as half-open ranges, because `BETWEEN 10 AND 20` / `BETWEEN 21 AND 30` would put a 20.5-minute ride in "Over 120 min" now that minutes are fractional.
- **The findings were hardcoded text.** "Members ride mostly on weekdays", "peaks around 8am and 5pm" and "March has the highest volume" were printed whether or not the data said so. They are now computed, and the median comparison was added next to the mean.
- **Fragile charts.** The monthly chart hardcoded `['January', 'February', 'March']` and the hourly chart skipped any hour with no rides, either of which would mislabel bars on a different extract. Both now index from the data.
- **Runs from the repo as committed.** The script reads the CSVs directly from `data/Divvy_Trips_2019-2020_Q1_csv.zip`; before, it failed unless you unzipped first.
- **Tests added** (`tests/test_cleaning.py`): one row per cleaning rule, the 24-hour boundary, mixed-type ride IDs, unknown rider labels, malformed timestamps, findings on synthetic data with known answers, and a dataset with no casual riders.
- Page typo fixed: member rides are 720,125 (one paragraph said 720,126).

**2026-09-16**
1. **The reported "90 min vs 13 min" ride-length finding was outlier-contaminated.** The only filter was `ride_length > 0`. The max ride was 10,632,022 seconds (~123 days), a bike that was never docked, and it pulled the casual mean to ~90 minutes. Adding a 24-hour cap gives 38 vs 11 min (3.4x). Only 4,249 of ~792,000 rows (0.5%) were affected.
2. **A 2019 column was mislabeled.** `bikeid` (a numeric bike ID) was renamed to `rideable_type` (a 2020 category like "docked_bike"). It is now `bike_id`.

## Repo hygiene

The extracted trip CSVs and `outputs/all_trips_clean.csv` are 100MB+ and gitignored; the zip in `data/` is the source and everything else regenerates from it.
