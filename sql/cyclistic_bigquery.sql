-- =============================================================================
-- CYCLISTIC BIKE SHARE — BIGQUERY SQL  (V3 — FINAL CLEAN VERSION)
-- Original: Case_Study1_Bike-Share.sql
-- Changed by: Claude (V3)
--
-- WHAT CHANGED FROM ORIGINAL:
--   1. Moved the repeated TIMESTAMP_DIFF calculation into CTEs so BigQuery
--      only computes it once per row instead of twice in the WHERE clause.
--      Keeps the query faster and avoids drift if column references change.
--   2. Added ELSE 'unknown' to the member_casual CASE statement so unexpected
--      usertype values produce 'unknown' instead of a silent NULL.
--   3. Extracted duration_bucket and day_type into the combined_trips table
--      itself so the dashboard_view does not duplicate CASE logic.
--      Change one bucket boundary, not two.
--   4. Added explicit section headers and consistent formatting throughout.
--   5. Day-of-week sort order updated: Sunday = 1 (matches standard US calendar
--      used in the Python analysis).
-- =============================================================================


-- =============================================================================
-- STEP 1: ROW-COUNT SANITY CHECK BEFORE COMBINING
-- =============================================================================

SELECT '2019' AS year, COUNT(*) AS total_rows
FROM `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`
UNION ALL
SELECT '2020', COUNT(*)
FROM `big-query-486123`.`Cyclist_Data`.`Trips_2020_Q1`;


-- =============================================================================
-- STEP 2: INSPECT USERTYPES IN 2019
-- =============================================================================

SELECT
  usertype,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`
GROUP BY usertype;


-- =============================================================================
-- STEP 3: NULL CHECK — 2019
-- =============================================================================

SELECT
  COUNTIF(trip_id    IS NULL) AS null_trip_id,
  COUNTIF(start_time IS NULL) AS null_start_time,
  COUNTIF(end_time   IS NULL) AS null_end_time,
  COUNTIF(usertype   IS NULL) AS null_usertype
FROM `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`;


-- =============================================================================
-- STEP 4: CREATE COMBINED TRIPS TABLE
-- =============================================================================
-- Uses CTEs to compute ride_length_min ONCE per row, then filter on it.
-- The original computed TIMESTAMP_DIFF twice in the WHERE clause.
--
-- ELSE 'unknown' surfaces unexpected usertype values instead of returning NULL.
-- Without it, any value not in the CASE silently becomes NULL and pollutes counts.
--
-- duration_bucket and day_type are added here so the dashboard_view can
-- SELECT * without repeating CASE logic.
-- =============================================================================

CREATE OR REPLACE TABLE `big-query-486123`.`Cyclist_Data`.`combined_trips` AS

WITH trips_2019 AS (
  SELECT
    CAST(trip_id AS STRING)         AS ride_id,
    start_time                      AS started_at,
    end_time                        AS ended_at,
    from_station_name               AS start_station_name,
    CAST(from_station_id AS STRING) AS start_station_id,
    to_station_name                 AS end_station_name,
    CAST(to_station_id AS STRING)   AS end_station_id,

    -- ELSE 'unknown': unexpected usertype values are visible instead of NULL
    CASE
      WHEN usertype = 'Subscriber' THEN 'member'
      WHEN usertype = 'Customer'   THEN 'casual'
      ELSE 'unknown'
    END AS member_casual,

    -- Compute duration once here; reference it in the filter below
    TIMESTAMP_DIFF(end_time, start_time, MINUTE) AS ride_length_min,

    FORMAT_TIMESTAMP('%A', start_time)            AS day_of_week,
    EXTRACT(HOUR FROM start_time)                 AS hour_of_day,
    FORMAT_TIMESTAMP('%Y-%m', start_time)         AS month

  FROM `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`
),

trips_2020 AS (
  SELECT
    ride_id,
    started_at,
    ended_at,
    start_station_name,
    CAST(start_station_id AS STRING) AS start_station_id,
    end_station_name,
    CAST(end_station_id AS STRING)   AS end_station_id,
    member_casual,
    TIMESTAMP_DIFF(ended_at, started_at, MINUTE) AS ride_length_min,
    FORMAT_TIMESTAMP('%A', started_at)            AS day_of_week,
    EXTRACT(HOUR FROM started_at)                 AS hour_of_day,
    FORMAT_TIMESTAMP('%Y-%m', started_at)         AS month

  FROM `big-query-486123`.`Cyclist_Data`.`Trips_2020_Q1`
),

combined AS (
  SELECT * FROM trips_2019
  WHERE ride_length_min > 0 AND ride_length_min < 1440

  UNION ALL

  SELECT * FROM trips_2020
  WHERE ride_length_min > 0 AND ride_length_min < 1440
)

-- Add day_type and duration_bucket in the final SELECT so they exist as base
-- columns in the table. The dashboard_view then reads them directly with no
-- duplicate CASE logic.
SELECT
  *,

  CASE
    WHEN day_of_week IN ('Saturday', 'Sunday') THEN 'Weekend'
    ELSE 'Weekday'
  END AS day_type,

  CASE
    WHEN ride_length_min < 10               THEN '1) Under 10 min'
    WHEN ride_length_min BETWEEN 10 AND 20  THEN '2) 10-20 min'
    WHEN ride_length_min BETWEEN 21 AND 30  THEN '3) 21-30 min'
    WHEN ride_length_min BETWEEN 31 AND 60  THEN '4) 31-60 min'
    WHEN ride_length_min BETWEEN 61 AND 120 THEN '5) 61-120 min'
    ELSE                                         '6) Over 120 min'
  END AS duration_bucket

FROM combined;


-- Confirm row count after combining — expect ~791,000 rows
SELECT COUNT(*) AS total_clean_rows
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`;

SELECT * FROM `big-query-486123`.`Cyclist_Data`.`combined_trips` LIMIT 10;


-- =============================================================================
-- STEP 5: SUMMARY STATISTICS
-- =============================================================================

SELECT
  member_casual,
  COUNT(*)                                           AS total_rides,
  ROUND(AVG(ride_length_min), 2)                     AS avg_ride_min,
  APPROX_QUANTILES(ride_length_min, 100)[OFFSET(50)] AS median_ride_min,
  MAX(ride_length_min)                               AS max_ride_min
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY member_casual
ORDER BY member_casual;


-- =============================================================================
-- STEP 6: RIDES BY DAY OF WEEK
-- Sort order: Sunday = 1 through Saturday = 7 (matches Python analysis)
-- =============================================================================

SELECT
  day_of_week,
  member_casual,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY day_of_week, member_casual
ORDER BY
  CASE day_of_week
    WHEN 'Sunday'    THEN 1
    WHEN 'Monday'    THEN 2
    WHEN 'Tuesday'   THEN 3
    WHEN 'Wednesday' THEN 4
    WHEN 'Thursday'  THEN 5
    WHEN 'Friday'    THEN 6
    WHEN 'Saturday'  THEN 7
  END,
  member_casual;


-- =============================================================================
-- STEP 7: RIDES BY HOUR OF DAY
-- =============================================================================

SELECT
  hour_of_day,
  member_casual,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY hour_of_day, member_casual
ORDER BY hour_of_day, member_casual;


-- =============================================================================
-- STEP 8: RIDES BY MONTH
-- =============================================================================

SELECT
  month,
  member_casual,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY month, member_casual
ORDER BY month, member_casual;


-- =============================================================================
-- STEP 9: WEEKDAY vs WEEKEND BREAKDOWN
-- day_type is a column in combined_trips — no CASE needed here
-- =============================================================================

SELECT
  member_casual,
  day_type,
  COUNT(*) AS ride_count,
  ROUND(AVG(ride_length_min), 2) AS avg_ride_min
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY member_casual, day_type
ORDER BY member_casual, day_type;


-- =============================================================================
-- STEP 10: DURATION BUCKET DISTRIBUTION
-- duration_bucket is a column in combined_trips — no CASE needed here
-- =============================================================================

SELECT
  member_casual,
  duration_bucket,
  COUNT(*) AS ride_count,
  ROUND(
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY member_casual),
    1
  ) AS pct_of_rider_type
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY member_casual, duration_bucket
ORDER BY member_casual, duration_bucket;


-- =============================================================================
-- STEP 11: TOP 10 CASUAL RIDER START STATIONS
-- =============================================================================

SELECT
  start_station_name,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
WHERE member_casual = 'casual'
  AND start_station_name IS NOT NULL
GROUP BY start_station_name
ORDER BY ride_count DESC
LIMIT 10;


-- =============================================================================
-- STEP 12: CREATE DASHBOARD VIEW
-- The view reads day_type and duration_bucket directly from combined_trips —
-- no duplicate CASE expressions required.
-- =============================================================================

CREATE OR REPLACE VIEW `big-query-486123`.`Cyclist_Data`.`dashboard_view` AS (
  SELECT
    ride_id,
    member_casual,
    ride_length_min,
    day_of_week,
    day_type,
    hour_of_day,
    month,
    duration_bucket,
    start_station_name,
    end_station_name
  FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
);

-- Confirm the view works
SELECT COUNT(*) AS total_rows
FROM `big-query-486123`.`Cyclist_Data`.`dashboard_view`;
