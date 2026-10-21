from pathlib import Path
import zipfile

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless: the script only writes PNGs
import matplotlib.pyplot as plt


DAYS_ORDER = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
WEEKEND = ["Saturday", "Sunday"]
MONTH_NAMES = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
               7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}

#Divvy's quality-check station: test rides, not customers
HQ_STATION = "HQ QR"

# TESTED 2026-09-16: the original filter (ride_length > 0, no upper bound)
# let a small number of extreme outliers through -- the max ride_length in
# this dataset is 10,632,022 seconds (about 123 days), almost certainly a
# bike that was never properly docked rather than a real ride. That pulled
# the casual-rider mean ride length up to ~90 minutes even though the
# median was ~23 minutes. A ride longer than a day is not representative
# user behavior, so 24 hours is the upper bound (same rule as the SQL).
MAX_RIDE_LENGTH_SEC = 24 * 60 * 60

# 2019 Divvy exports use different column names and rider labels than 2020+.
# `bikeid` is a numeric bike ID, not the same field as 2020's `rideable_type`
# (a category like "docked_bike"), so it is renamed to bike_id, not merged.
COLUMNS_2019_TO_2020 = {
    'trip_id': 'ride_id',
    'bikeid': 'bike_id',
    'start_time': 'started_at',
    'end_time': 'ended_at',
    'from_station_name': 'start_station_name',
    'from_station_id': 'start_station_id',
    'to_station_name': 'end_station_name',
    'to_station_id': 'end_station_id',
    'usertype': 'member_casual',
}
RIDER_LABELS = {'Subscriber': 'member', 'Customer': 'casual', 'member': 'member', 'casual': 'casual'}

#Dropped because 2020 exports no longer carry them
DROPPED_COLUMNS = ['start_lat', 'start_lng', 'end_lat', 'end_lng', 'birthyear', 'gender', 'tripduration']


def combine_quarters(q1_2019, q1_2020):
    #Reconcile the two schemas and stack them into one frame
    q1_2019 = q1_2019.rename(columns=COLUMNS_2019_TO_2020)
    q1_2019['ride_id'] = q1_2019['ride_id'].astype(str)
    if 'bike_id' in q1_2019:
        q1_2019['bike_id'] = q1_2019['bike_id'].astype(str)
    q1_2020 = q1_2020.copy()
    q1_2020['ride_id'] = q1_2020['ride_id'].astype(str)
    all_trips = pd.concat([q1_2019, q1_2020], ignore_index=True)
    return all_trips.drop(columns=DROPPED_COLUMNS, errors='ignore')


def clean_trips(all_trips):
    """Normalize labels, derive date fields and ride length, then drop bad rows.

    Returns (clean frame, dict of how many rows each rule removed). Rules run in
    order and a row is counted against the first rule it fails.
    """
    df = all_trips.copy()
    df['member_casual'] = df['member_casual'].map(RIDER_LABELS)
    #format="mixed" + coerce: a malformed timestamp becomes NaT and is dropped below, not a crash
    df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce', format='mixed')
    df['ended_at'] = pd.to_datetime(df['ended_at'], errors='coerce', format='mixed')
    df['ride_length'] = (df['ended_at'] - df['started_at']).dt.total_seconds()

    rules = [
        ('unknown rider type', df['member_casual'].isna()),
        ('unparseable timestamp', df['ride_length'].isna()),
        ('HQ QR test ride', df['start_station_name'].eq(HQ_STATION)),
        ('zero or negative length', df['ride_length'] <= 0),
        ('longer than 24 hours', df['ride_length'] > MAX_RIDE_LENGTH_SEC),
    ]
    dropped = {}
    keep = pd.Series(True, index=df.index)
    for name, bad in rules:
        hit = keep & bad.fillna(False)
        dropped[name] = int(hit.sum())
        keep &= ~hit
    df = df[keep].copy()

    df['date'] = df['started_at'].dt.date
    df['month'] = df['started_at'].dt.month
    df['day'] = df['started_at'].dt.day
    df['year'] = df['started_at'].dt.year
    df['hour'] = df['started_at'].dt.hour
    #Categorical so every groupby sorts Sunday..Saturday
    df['day_of_week'] = pd.Categorical(df['started_at'].dt.day_name(), categories=DAYS_ORDER, ordered=True)
    df['ride_length_min'] = df['ride_length'] / 60
    return df, dropped


def compute_findings(df):
    #Every number the write-up quotes comes from here, so the text can't drift from the data
    by_type = df.groupby('member_casual', observed=True)
    rides = by_type['ride_id'].count()
    weekend = df['day_of_week'].isin(WEEKEND)
    weekday = ~weekend
    #Rides per average day, so 5 weekdays vs 2 weekend days compare fairly
    weekend_per_day = df[weekend].groupby('member_casual')['ride_id'].count() / 2
    weekday_per_day = df[weekday].groupby('member_casual')['ride_id'].count() / 5
    hourly = df[weekday].groupby(['member_casual', 'hour'])['ride_id'].count()
    monthly = df.groupby(['member_casual', 'month'])['ride_id'].count()

    findings = {'total_rides': int(rides.sum())}
    for rider in ('member', 'casual'):
        if rider not in rides.index:
            continue
        lengths = df.loc[df['member_casual'] == rider, 'ride_length_min']
        hours = hourly.loc[rider] if rider in hourly.index.get_level_values(0) else pd.Series(dtype=float)
        months = monthly.loc[rider]
        findings[rider] = {
            'rides': int(rides[rider]),
            'share_of_rides': float(rides[rider] / rides.sum()),
            'mean_min': float(lengths.mean()),
            'median_min': float(lengths.median()),
            'weekend_share': float(weekend[df['member_casual'] == rider].mean()),
            'weekend_vs_weekday_per_day': float(weekend_per_day.get(rider, 0) / weekday_per_day[rider])
                if weekday_per_day.get(rider, 0) else float('nan'),
            'weekday_peak_hours': sorted(int(h) for h in hours.nlargest(2).index),
            'peak_month': int(months.idxmax()),
        }
    if 'member' in findings and 'casual' in findings:
        findings['mean_ratio'] = findings['casual']['mean_min'] / findings['member']['mean_min']
        findings['median_ratio'] = findings['casual']['median_min'] / findings['member']['median_min']
    return findings


def format_findings(f):
    m, c = f['member'], f['casual']
    month = MONTH_NAMES[m['peak_month']] if m['peak_month'] == c['peak_month'] else \
        f"{MONTH_NAMES[m['peak_month']]} (members) / {MONTH_NAMES[c['peak_month']]} (casual)"
    return f"""
1. Members take {m['share_of_rides']:.0%} of rides, but casual riders ride longer:
   median {c['median_min']:.0f} min vs {m['median_min']:.0f} min ({f['median_ratio']:.1f}x),
   mean {c['mean_min']:.0f} min vs {m['mean_min']:.0f} min ({f['mean_ratio']:.1f}x).
   The median is the fairer comparison; ride length is right-skewed.

2. Casual riders are weekend riders: {c['weekend_share']:.0%} of their rides fall on
   Sat/Sun, and they ride {c['weekend_vs_weekday_per_day']:.1f}x as much per weekend day as per weekday.
   Members are the opposite: {m['weekend_share']:.0%} weekend, {m['weekend_vs_weekday_per_day']:.1f}x per day.

3. On weekdays members peak at {', '.join(f'{h}:00' for h in m['weekday_peak_hours'])}
   (commute hours); casual riders peak at {', '.join(f'{h}:00' for h in c['weekday_peak_hours'])}.

4. Busiest month: {month}. This is Q1 only (Jan-Mar), so it shows
   the end of winter, not a full seasonal picture.
"""


def plot_grouped_bar(ax, categories, member_vals, casual_vals, member_color, casual_color, title, xlabel, ylabel):
    #Helper to build side-by-side bar charts for member vs casual comparisons.
    x = range(len(categories))
    ax.bar([i - 0.2 for i in x], member_vals, width=0.4, label='Member', color=member_color, alpha=0.85)
    ax.bar([i + 0.2 for i in x], casual_vals, width=0.4, label='Casual', color=casual_color, alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(categories, rotation=30, ha='right')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)


def load_quarter(data_dir, name):
    #The repo ships the CSVs zipped; read straight from the zip if they aren't extracted
    csv = data_dir / name
    if csv.exists():
        return pd.read_csv(csv)
    for archive in sorted(data_dir.glob('*.zip')):
        with zipfile.ZipFile(archive) as zf:
            if name in zf.namelist():
                with zf.open(name) as fh:
                    return pd.read_csv(fh)
    raise FileNotFoundError(f"{name} not found in {data_dir} (as a CSV or inside a .zip)")


def main():
    #Script lives in python/, CSVs live in data/, outputs go to outputs/ — all siblings at project root
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    output_folder = project_root / "outputs"
    output_folder.mkdir(exist_ok=True)

    member_color = '#4472C4'
    casual_color = '#ED7D31'

    q1_2019 = load_quarter(data_dir, "Divvy_Trips_2019_Q1.csv")
    q1_2020 = load_quarter(data_dir, "Divvy_Trips_2020_Q1.csv")
    print(f"Loaded {len(q1_2019):,} rows (Q1 2019) and {len(q1_2020):,} rows (Q1 2020)")

    all_trips = combine_quarters(q1_2019, q1_2020)
    print("Rider labels before cleaning:\n", all_trips['member_casual'].value_counts())

    all_trips_v2, dropped = clean_trips(all_trips)
    print(f"\nKept {len(all_trips_v2):,} of {len(all_trips):,} rows. Dropped:")
    for rule, n in dropped.items():
        print(f"  {rule:<26}{n:>8,}")
    #Row conservation: every input row is either kept or counted against one rule
    assert len(all_trips_v2) + sum(dropped.values()) == len(all_trips)

    print("\nRide length (minutes) by rider type:\n",
          all_trips_v2.groupby('member_casual')['ride_length_min'].agg(['count', 'mean', 'median', 'max', 'min']).round(1))

    #VISUALIZATIONS

    #Chart 1: Number of Rides by Day of Week
    rides_by_day = (all_trips_v2.groupby(['member_casual', 'day_of_week'], observed=False)['ride_id']
                    .count().unstack(0).reindex(DAYS_ORDER).fillna(0))
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_grouped_bar(
        ax, DAYS_ORDER,
        rides_by_day.get('member', 0), rides_by_day.get('casual', 0),
        member_color, casual_color,
        'Number of Rides by Day of Week', 'Day of Week', 'Number of Rides'
    )
    plt.tight_layout()
    plt.savefig(output_folder / 'chart1_rides_by_day.png', dpi=150)
    plt.close()
    print("\nSaved chart1_rides_by_day.png")

    #Chart 2: Median Ride Duration by Day of Week
    #Median, not mean: one undocked bike can drag a mean by minutes
    duration_by_day = (all_trips_v2.groupby(['member_casual', 'day_of_week'], observed=False)['ride_length_min']
                       .median().unstack(0).reindex(DAYS_ORDER))
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(DAYS_ORDER, duration_by_day['member'], marker='o', linewidth=2, label='Member', color=member_color)
    ax.plot(DAYS_ORDER, duration_by_day['casual'], marker='o', linewidth=2, label='Casual', color=casual_color)
    ax.set_title('Median Ride Duration by Day of Week (minutes)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Median Duration (minutes)')
    ax.set_ylim(bottom=0)
    ax.legend()
    ax.grid(alpha=0.3)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig(output_folder / 'chart2_avg_duration_by_day.png', dpi=150)
    plt.close()
    print("Saved chart2_avg_duration_by_day.png")

    #Chart 3: Rides by Hour of Day
    #Looking for commuter peaks (8am / 5pm) vs casual riders spread through the day.
    #Reindexed to 0-23 so an hour with no rides plots as 0 instead of being skipped
    rides_by_hour = all_trips_v2.groupby(['member_casual', 'hour'])['ride_id'].count().reset_index()
    rides_by_hour.columns = ['member_casual', 'hour', 'number_of_rides']
    hourly_wide = rides_by_hour.pivot(index='hour', columns='member_casual', values='number_of_rides') \
        .reindex(range(24)).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(hourly_wide.index, hourly_wide['member'], marker='o', linewidth=2, label='Member', color=member_color)
    ax.plot(hourly_wide.index, hourly_wide['casual'], marker='o', linewidth=2, label='Casual', color=casual_color)
    ax.set_title('Number of Rides by Hour of Day', fontsize=14, fontweight='bold')
    ax.set_xlabel('Hour of Day (0 = midnight)')
    ax.set_ylabel('Number of Rides')
    ax.set_xticks(range(0, 24))
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_folder / 'chart3_rides_by_hour.png', dpi=150)
    plt.close()
    print("Saved chart3_rides_by_hour.png")

    #Chart 4: Monthly Ride Volume
    #Months come from the data (not a hardcoded Jan-Mar list) so the bars always line up with their labels
    rides_by_month = all_trips_v2.groupby(['member_casual', 'month'])['ride_id'].count().reset_index()
    rides_by_month.columns = ['member_casual', 'month', 'number_of_rides']
    monthly_wide = rides_by_month.pivot(index='month', columns='member_casual', values='number_of_rides').fillna(0)

    fig, ax = plt.subplots(figsize=(8, 5))
    plot_grouped_bar(
        ax, [MONTH_NAMES[m] for m in monthly_wide.index],
        monthly_wide['member'].values, monthly_wide['casual'].values,
        member_color, casual_color,
        'Monthly Ride Volume - Q1 Only', 'Month', 'Number of Rides'
    )
    plt.tight_layout()
    plt.savefig(output_folder / 'chart4_rides_by_month.png', dpi=150)
    plt.close()
    print("Saved chart4_rides_by_month.png")

    #Chart 5: Top 10 Start Stations for Casual Riders
    #Where casual riders start their trips — useful for targeting ads or promotions
    top_casual_stations = (
        all_trips_v2[all_trips_v2['member_casual'] == 'casual']
        .groupby('start_station_name')['ride_id']
        .count()
        .sort_values(ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    top_casual_stations.sort_values().plot(kind='barh', ax=ax, color=casual_color, alpha=0.85)
    ax.set_title('Top 10 Start Stations for Casual Riders', fontsize=14, fontweight='bold')
    ax.set_xlabel('Number of Rides')
    ax.set_ylabel('')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_folder / 'chart5_top_stations_casual.png', dpi=150)
    plt.close()
    print("Saved chart5_top_stations_casual.png")

    #EXPORT CLEANED DATA

    all_trips_v2.to_csv(output_folder / 'all_trips_clean.csv', index=False)
    print("\nSaved all_trips_clean.csv")

    #Summary by rider type and day — good for Tableau
    summary_by_day = all_trips_v2.groupby(['member_casual', 'day_of_week'], observed=False).agg(
        number_of_rides=('ride_id', 'count'),
        avg_ride_length_min=('ride_length_min', 'mean'),
        median_ride_length_min=('ride_length_min', 'median'),
    ).reset_index()
    summary_by_day.to_csv(output_folder / 'summary_by_day.csv', index=False)
    print("Saved summary_by_day.csv")

    rides_by_month.to_csv(output_folder / 'summary_by_month.csv', index=False)
    print("Saved summary_by_month.csv")

    rides_by_hour.to_csv(output_folder / 'summary_by_hour.csv', index=False)
    print("Saved summary_by_hour.csv")

    #KEY FINDINGS
    #Answering the business question: "How do annual members and casual riders use Cyclistic bikes differently?"
    findings = compute_findings(all_trips_v2)
    print("\nKEY FINDINGS")
    print(format_findings(findings))

    print("TOP 3 RECOMMENDATIONS")
    print("""
1. Create a weekend or seasonal membership option to appeal to casual
   riders -- they're already using the bikes on weekends, so a pass
   that fits that pattern might be an easier sell than a full annual membership.

2. Focus marketing at the top casual rider start stations (chart 5) --
   that's where they already are, so ads or promos there make sense.

3. Show casual riders how much they'd save with a membership given how
   long their rides tend to be -- longer rides cost more on single-ride
   or day passes so the value case could be pretty strong.
""")

    print("All output files saved to:", output_folder)


if __name__ == "__main__":
    main()
