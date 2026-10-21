"""Edge-case tests for the cleaning and findings logic, on hand-built rows.

Run: python -m pytest tests/
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
from Cyclist_Analysis_Python import (  # noqa: E402
    MAX_RIDE_LENGTH_SEC, clean_trips, combine_quarters, compute_findings, format_findings,
)


def q2019(rows):
    return pd.DataFrame(rows, columns=['trip_id', 'start_time', 'end_time', 'bikeid',
                                       'from_station_name', 'usertype', 'gender', 'birthyear'])


def q2020(rows):
    return pd.DataFrame(rows, columns=['ride_id', 'started_at', 'ended_at', 'rideable_type',
                                       'start_station_name', 'member_casual', 'start_lat'])


def test_each_bad_row_is_dropped_by_exactly_one_rule():
    a = q2019([
        (1, '2019-01-06 08:00:00', '2019-01-06 08:10:00', 11, 'A', 'Subscriber', 'M', 1980),  # kept
        (2, '2019-01-06 08:00:00', '2019-01-06 08:00:00', 12, 'A', 'Customer', None, None),   # zero length
        (3, '2019-01-06 08:00:00', '2019-01-05 08:00:00', 13, 'A', 'Customer', None, None),   # negative
        (4, '2019-01-06 08:00:00', '2019-01-08 08:00:00', 14, 'A', 'Customer', None, None),   # > 24h
        (5, '2019-01-06 08:00:00', '2019-01-06 08:30:00', 15, 'A', 'Dependent', None, None),  # unknown type
    ])
    b = q2020([
        ('x1', '2020-03-01 17:00:00', '2020-03-01 17:40:00', 'docked_bike', 'B', 'casual', 41.9),  # kept
        ('x2', '2020-03-01 17:00:00', '2020-03-01 17:05:00', 'docked_bike', 'HQ QR', 'casual', 41.9),
        ('x3', 'not a time', '2020-03-01 17:05:00', 'docked_bike', 'B', 'member', 41.9),
        ('x4', '2020-03-01 17:00:00', None, 'docked_bike', 'B', 'member', 41.9),
    ])
    combined = combine_quarters(a, b)
    clean, dropped = clean_trips(combined)
    assert sorted(clean['ride_id']) == ['1', 'x1']
    assert dropped == {'unknown rider type': 1, 'unparseable timestamp': 2, 'HQ QR test ride': 1,
                       'zero or negative length': 2, 'longer than 24 hours': 1}
    assert len(clean) + sum(dropped.values()) == len(combined)
    # 2019 labels are normalized to the 2020 vocabulary
    assert set(clean['member_casual']) == {'member', 'casual'}
    # Columns 2020 dropped are gone; bikeid became bike_id, not rideable_type
    assert not {'gender', 'birthyear', 'start_lat'} & set(clean.columns)
    assert clean.loc[clean.ride_id == '1', 'bike_id'].item() == '11'
    assert pd.isna(clean.loc[clean.ride_id == '1', 'rideable_type'].item())


def test_24_hour_boundary_is_inclusive():
    end = pd.Timestamp('2019-01-06 08:00:00') + pd.Timedelta(seconds=MAX_RIDE_LENGTH_SEC)
    a = q2019([
        (1, '2019-01-06 08:00:00', str(end), 1, 'A', 'Subscriber', None, None),
        (2, '2019-01-06 08:00:00', str(end + pd.Timedelta(seconds=1)), 1, 'A', 'Subscriber', None, None),
    ])
    clean, _ = clean_trips(combine_quarters(a, q2020([])))
    assert list(clean['ride_id']) == ['1']


def test_ride_id_types_stack_cleanly():
    # 2019 ids are ints, 2020 ids are hex strings; both must survive as strings
    a = q2019([(10, '2019-01-07 08:00:00', '2019-01-07 08:10:00', 1, 'A', 'Subscriber', None, None)])
    b = q2020([('ABC', '2020-01-07 08:00:00', '2020-01-07 08:10:00', 'docked_bike', 'A', 'member', 0.0)])
    clean, _ = clean_trips(combine_quarters(a, b))
    assert clean['ride_id'].tolist() == ['10', 'ABC']


def _synthetic_trips():
    # Members: short weekday commutes at 8:00 and 17:00. Casual: long weekend rides at noon.
    rows = []
    rid = 0
    for day in pd.date_range('2020-03-02', '2020-03-08'):  # Mon..Sun
        weekend = day.day_name() in ('Saturday', 'Sunday')
        for hour in (8, 17):
            for _ in range(1 if weekend else 10):
                rid += 1
                start = day + pd.Timedelta(hours=hour)
                rows.append((f'm{rid}', str(start), str(start + pd.Timedelta(minutes=10)), 'd', 'S', 'member', 0))
        for _ in range(10 if weekend else 1):
            rid += 1
            start = day + pd.Timedelta(hours=12)
            rows.append((f'c{rid}', str(start), str(start + pd.Timedelta(minutes=40)), 'd', 'S', 'casual', 0))
    return clean_trips(combine_quarters(q2019([]), q2020(rows)))[0]


def test_findings_are_computed_from_the_data():
    f = compute_findings(_synthetic_trips())
    assert f['member']['median_min'] == pytest.approx(10)
    assert f['casual']['median_min'] == pytest.approx(40)
    assert f['median_ratio'] == pytest.approx(4)
    assert f['member']['weekday_peak_hours'] == [8, 17]
    assert f['casual']['weekend_share'] == pytest.approx(20 / 25)
    assert f['casual']['weekend_vs_weekday_per_day'] == pytest.approx(10)
    assert f['member']['weekend_vs_weekday_per_day'] == pytest.approx(0.1)
    assert f['member']['peak_month'] == 3
    text = format_findings(f)
    assert 'median 40 min vs 10 min (4.0x)' in text


def test_findings_without_casual_riders_do_not_crash():
    df = _synthetic_trips()
    f = compute_findings(df[df['member_casual'] == 'member'])
    assert 'casual' not in f and 'median_ratio' not in f
    assert f['member']['share_of_rides'] == 1.0
