# 91% of rides come from members.
### So why are casual riders the conversion opportunity?

> **[Live Report](https://jbattohokson.github.io/Cyclistic_Bike_Share_Analysis/Bike-Share_Analysis.html)** | [GitHub Repo](https://github.com/jbattohokson/Cyclistic_Bike_Share_Analysis)

---

## Executive Summary

Google Data Analytics Capstone project. Cyclistic is a fictional Chicago-based bike-share with 5,800+ bikes and 600+ docking stations. Annual members already generate more profit per rider than casual users — the strategic question is not whether to convert casual riders, but which ones to target, when, and with what message.

This analysis of 791,264 Q1 trips (Q1 2019 and Q1 2020) shows that casual riders and annual members use the system in fundamentally different ways. Members are commuters. Casual riders are weekend leisure cyclists. Those two groups need different conversion arguments, different timing, and different product structures. The highest-value conversion opportunity is not a discount — it is a product that matches how casual riders actually use the system.

| Metric | Value |
|--------|-------|
| Total rides analyzed | 791,264 |
| Annual member share | 91% (720,126 rides) |
| Casual rider share | 9% (71,138 rides) |
| Avg casual ride duration | 36.5 min |
| Avg member ride duration | 11.4 min |
| Duration gap | 3.2x longer for casual riders |
| Casual peak days | Saturday and Sunday |
| Casual peak hours | 10 AM – 4 PM |

---

## Tools & Technologies

| Tool | Purpose |
|------|---------|
| Python (pandas, Matplotlib) | Data cleaning, feature engineering, behavioral analysis, visualization |
| SQL (BigQuery) | Large-scale aggregation, view creation, segment queries |
| Tableau | Member vs. casual ridership dashboards, temporal and geographic breakdowns |

---

## Findings: Four behavioral differences worth examining for conversion strategy

### Members commute. Casual riders explore. These require different conversion arguments.
Members account for 91% of Q1 rides (720,126) while casual riders represent 9% (71,138). But casual riders take rides that average 36.5 minutes versus 11.4 minutes for members — a 3.2x gap. Members show the classic dual-peak commute pattern: 7–9 AM and 5–6 PM on weekdays. Casual riders show a single broad midday peak on weekends. A casual rider taking a 36-minute Saturday ride does not need a commuter pitch — messaging focused on city exploration and longer-ride value is more relevant than cost-per-commute savings.

| Metric | Member | Casual |
|--------|--------|--------|
| Total rides (Q1) | 720,126 (91%) | 71,138 (9%) |
| Avg ride duration | 11.4 min | 36.5 min |
| Median ride duration | 8.5 min | 22.0 min |
| Peak days | Tue–Thu | Sat–Sun |
| Peak hours | 7–9 AM, 5–6 PM | 10 AM – 4 PM |

### The conversion window is Saturday and Sunday, 10 AM to 4 PM
Casual ridership peaks Saturday and Sunday while member ridership drops sharply on those same days. The overlap is minimal — these are two distinct populations using the same infrastructure at different times. The optimal conversion moment is mid-ride on a Saturday or Sunday, when a casual rider is actively engaged with the product and physically present at a docking station. In-app prompts and docking station signage triggered at ride completion have higher conversion probability than weekday email campaigns.

### Casual riders who use the system frequently likely pay more annually than members do
At casual single-ride rates of approximately $3.30 per trip (Divvy 2019–2020 pricing), a rider taking two rides per weekend across 12 months spends roughly $343 annually. Annual membership at $108/year saves that rider approximately $235. The math favors membership for any casual rider using the system more than 33 times per year — less than once per week. A cost comparison calculator showing what a casual rider's Q1 ride pattern would have cost at casual rates versus annual membership is the most direct conversion argument available. *Note: these are approximate 2019 Divvy pricing figures; current rates should be substituted before use in any live campaign.*

### Casual ridership is more seasonal — which means conversion timing matters by month
Casual ridership grows more steeply as Q1 progresses into warmer months, while members maintain more consistent ridership through the same period. Casual riders are weather-sensitive in a way members are not — consistent with leisure use patterns and a likely tourist component. Conversion campaigns launched in late Q1 (March) reach casual riders at the moment their ridership is increasing, before they settle into a summer pattern without membership.

---

## Recommendations: Three conversion levers ranked by expected reach

### Weekend conversion campaigns at peak usage moments
Target casual riders at docking stations and via in-app prompt on Saturday and Sunday, triggered immediately after ride completion — the highest-engagement moment. A time-limited discount for converting during or after a weekend ride reduces friction at the point of maximum product satisfaction.

### Create a leisure or weekend membership tier
Annual membership is priced and positioned for commuters. A "Weekend Pass" or "Leisure Membership" priced between casual per-trip rates and annual membership reduces the commitment barrier, creates an upsell path to annual membership, and generates revenue from a segment that currently pays per-trip. Pricing target: between casual rates and annual membership cost.

### Run leisure-focused ads between 10 AM and 4 PM on weekends
Messaging should focus on exploration and longer-ride value, not commuting efficiency. Partner with local tourism and event platforms to reach casual riders planning weekend activities. Match channel timing to when casual riders are active — not when members are.

---

## Data Scope and Cleaning

| Dimension | Value |
|-----------|-------|
| Dataset | Divvy / Motivate International Inc. — public license |
| Period | Q1 2019 (365,069 rows) and Q1 2020 (426,886 rows) |
| Final clean dataset | 791,264 rides (692 rows removed, under 0.1%) |
| Exclusions | Ride lengths ≤0 min (negative/zero durations); ride lengths ≥1,440 min (likely maintenance trips) |
| Schema standardization | 2019 column names unified with 2020 schema (trip_id → ride_id, usertype → member_casual) |
| Engineered features | ride_length_min, day_of_week, hour, month |

**Scope limitations:** This analysis covers Q1 only (January–March). Full-year data would strengthen seasonal findings, particularly summer leisure riding peaks. Data privacy prevents linking rides to individual users — lifetime value comparisons and funnel tracking are not possible with this dataset. A/B testing the weekend conversion campaign against a control group is recommended before full rollout.
