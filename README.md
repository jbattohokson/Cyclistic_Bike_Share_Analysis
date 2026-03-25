# 🚲 Cyclistic Bike-Share Analysis

**Google Data Analytics Capstone Project**

> *"How do annual members and casual riders use Cyclistic bikes differently?"*

---

## Overview

Cyclistic is a fictional Chicago-based bike-share company with 5,800+ bikes and 600+ docking stations. This analysis examines Q1 2019 and Q1 2020 ride data (791,000+ trips) to identify behavioral differences between annual members and casual riders.

---

## Tools & Technologies

| Tool | Purpose |
|---|---|
| **Python** (pandas, Matplotlib) | Data wrangling, cleaning, EDA, visualization |
| **BigQuery SQL** | Large-scale data querying, aggregation, view creation |
| **Tableau** | Interactive dashboard and final deliverables |

---

## Data Source

- **Divvy Trips Q1 2019** — 365,069 rows
- **Divvy Trips Q1 2020** — 426,887 rows
- Source: [Divvy Historical Trip Data](https://divvy-tripdata.s3.amazonaws.com/index.html) (made available under Motivate International Inc. license)

---

## Methodology

1. **Prepare** — Loaded and inspected both quarterly CSVs; identified schema mismatches between 2019 and 2020 column naming conventions
2. **Process** — Renamed 2019 columns to match 2020; standardized member type labels (`Subscriber` → `member`, `Customer` → `casual`); computed `ride_length` and extracted date parts; removed quality issues
3. **Analyze** — Grouped by rider type and day of week, hour of day, and month; computed average ride duration and ride counts
4. **Share** — Built 5 Python charts and an interactive Tableau dashboard; exported clean CSVs for Tableau

---

## Key Findings

| Metric | Members | Casual Riders |
|---|---|---|
| Share of total rides | ~77% | ~23% |
| Avg ride duration | ~13 min | ~59 min |
| Peak day | Weekdays (commuting pattern) | Weekends (leisure pattern) |
| Peak hours | 8am and 5pm (rush hour) | Spread throughout day |

**Casual riders take 4.5× longer trips on average**, suggesting they are tourists or leisure users rather than commuters.

---

## Recommendations

1. **Weekend/Seasonal Pass** — Create a membership tier targeting weekend-only or warm-season riders, matching how casual riders already use the service
2. **Station-Based Marketing** — Focus promotions at the top 10 casual rider start stations where they're already concentrated
3. **Value Messaging** — Show casual riders their potential savings: given their longer average ride time, a membership vs. single-ride pricing makes a strong financial case

---

## Repository Contents

```
├── Cyclist_Analysis_V1.py          # Full Python pipeline (load → clean → analyze → visualize → export)
├── Case_Study1_Bike-Share.sql      # BigQuery SQL (combine, clean, aggregate, dashboard view)
├── Cyclistic_Bike_Share_Viz_V1.twbx # Tableau workbook
├── Cyclistic_Analysis_Report.pdf   # Full written analysis report
├── Datasets/
│   ├── Divvy_Trips_2019_Q1.csv
│   └── Divvy_Trips_2020_Q1.csv
└── outputs/                        # Python-generated charts and cleaned CSVs
```

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas matplotlib

# 2. Place CSVs in the Datasets/ folder

# 3. Run the Python pipeline
python "Python Code/Cyclist_Analysis_V1.py"
```

Charts and cleaned CSVs will be saved to `outputs/`. Connect Tableau to `all_trips_clean.csv` or `summary_by_day.csv` for dashboard use.

---

*Part of the Google Data Analytics Professional Certificate capstone.*