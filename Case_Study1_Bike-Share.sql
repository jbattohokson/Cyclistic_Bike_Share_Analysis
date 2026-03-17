SELECT
  '2019' AS year,
  COUNT(*) AS total_rows
FROM
  `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`
UNION ALL
SELECT
  '2020' AS year,
  COUNT(*) AS total_rows
FROM
  `big-query-486123`.`Cyclist_Data`.`Trips_2020_Q1`;


  SELECT 
    usertype,
    COUNT(*) AS ride_count
  FROM 
  `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`
  Group by usertype;


SELECT
  COUNTIF(trip_id    IS NULL) AS null_trip_id,
  COUNTIF(start_time IS NULL) AS null_start_time,
  COUNTIF(end_time   IS NULL) AS null_end_time,
  COUNTIF(usertype   IS NULL) AS null_usertype
FROM `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`;


CREATE OR REPLACE TABLE `big-query-486123`.`Cyclist_Data`.`combined_trips` AS (

  -- 2019 data: rename columns and remap rider type values
  -- CAST(trip_id AS STRING) converts the numeric ID to text because
  -- 2020 uses text IDs — both columns must be the same type to UNION
  SELECT
    CAST(trip_id AS STRING)         AS ride_id,
    start_time                      AS started_at,
    end_time                        AS ended_at,
    from_station_name               AS start_station_name,
    CAST(from_station_id AS STRING) AS start_station_id,
    to_station_name                 AS end_station_name,
    CAST(to_station_id AS STRING)   AS end_station_id,

    -- CASE WHEN = SQL's version of if/else
    CASE
      WHEN usertype = 'Subscriber' THEN 'member'
      WHEN usertype = 'Customer'   THEN 'casual'
    END AS member_casual,

    -- Ride duration in minutes (equivalent to =D2-C2 in Excel)
    TIMESTAMP_DIFF(end_time, start_time, MINUTE) AS ride_length_min,

    -- Full day name e.g. "Monday" (equivalent to =WEEKDAY() in Excel)
    FORMAT_TIMESTAMP('%A', start_time)            AS day_of_week,

    -- Hour of day 0-23
    EXTRACT(HOUR FROM start_time)                 AS hour_of_day,

    -- Year-month label e.g. "2019-01"
    FORMAT_TIMESTAMP('%Y-%m', start_time)         AS month

  FROM `big-query-486123`.`Cyclist_Data`.`Trips_2019_Q1`

  -- Remove data errors: zero/negative durations and 24hr+ maintenance rides
  WHERE TIMESTAMP_DIFF(end_time, start_time, MINUTE) > 0
    AND TIMESTAMP_DIFF(end_time, start_time, MINUTE) < 1440

  UNION ALL

  -- 2020 data: already uses the right column names, just add calculated columns
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

  WHERE TIMESTAMP_DIFF(ended_at, started_at, MINUTE) > 0
    AND TIMESTAMP_DIFF(ended_at, started_at, MINUTE) < 1440
);


-- Confirm it worked — expect ~791,000 rows
SELECT COUNT(*) AS total_clean_rows
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`;

SELECT *
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
LIMIT 10;


SELECT
  member_casual,
  COUNT(*)                                           AS total_rides,
  ROUND(AVG(ride_length_min), 2)                     AS avg_ride_min,
  APPROX_QUANTILES(ride_length_min, 100)[OFFSET(50)] AS median_ride_min,
  MAX(ride_length_min)                               AS max_ride_min
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY member_casual
ORDER BY member_casual;

SELECT
  day_of_week,
  member_casual,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY day_of_week, member_casual
ORDER BY
  CASE day_of_week
    WHEN 'Monday'    THEN 1
    WHEN 'Tuesday'   THEN 2
    WHEN 'Wednesday' THEN 3
    WHEN 'Thursday'  THEN 4
    WHEN 'Friday'    THEN 5
    WHEN 'Saturday'  THEN 6
    WHEN 'Sunday'    THEN 7
  END,
  member_casual;


  SELECT
  hour_of_day,
  member_casual,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY hour_of_day, member_casual
ORDER BY hour_of_day, member_casual;


SELECT
  month,
  member_casual,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY month, member_casual
ORDER BY month, member_casual;


SELECT
  member_casual,
  CASE
    WHEN day_of_week IN ('Saturday', 'Sunday') THEN 'Weekend'
    ELSE 'Weekday'
  END AS day_type,
  COUNT(*) AS ride_count,
  ROUND(AVG(ride_length_min), 2) AS avg_ride_min
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY member_casual, day_type
ORDER BY member_casual, day_type;


SELECT
  member_casual,
  CASE
    WHEN ride_length_min < 10               THEN '1) Under 10 min'
    WHEN ride_length_min BETWEEN 10 AND 20  THEN '2) 10-20 min'
    WHEN ride_length_min BETWEEN 21 AND 30  THEN '3) 21-30 min'
    WHEN ride_length_min BETWEEN 31 AND 60  THEN '4) 31-60 min'
    WHEN ride_length_min BETWEEN 61 AND 120 THEN '5) 61-120 min'
    ELSE                                         '6) Over 120 min'
  END AS duration_bucket,
  COUNT(*) AS ride_count,
  ROUND(
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY member_casual),
    1
  ) AS pct_of_rider_type
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
GROUP BY member_casual, duration_bucket
ORDER BY member_casual, duration_bucket;


SELECT
  start_station_name,
  COUNT(*) AS ride_count
FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
WHERE member_casual = 'casual'
  AND start_station_name IS NOT NULL
GROUP BY start_station_name
ORDER BY ride_count DESC
LIMIT 10;


CREATE OR REPLACE VIEW `big-query-486123`.`Cyclist_Data`.`dashboard_view` AS (
  SELECT
    ride_id,
    member_casual,
    ride_length_min,
    day_of_week,
    hour_of_day,
    month,
    start_station_name,
    end_station_name,

    -- Weekday/weekend flag for easy filtering in Looker Studio
    CASE
      WHEN day_of_week IN ('Saturday', 'Sunday') THEN 'Weekend'
      ELSE 'Weekday'
    END AS day_type,

    -- Duration bucket for bar charts in Looker Studio
    CASE
      WHEN ride_length_min < 10               THEN '1) Under 10 min'
      WHEN ride_length_min BETWEEN 10 AND 20  THEN '2) 10-20 min'
      WHEN ride_length_min BETWEEN 21 AND 30  THEN '3) 21-30 min'
      WHEN ride_length_min BETWEEN 31 AND 60  THEN '4) 31-60 min'
      WHEN ride_length_min BETWEEN 61 AND 120 THEN '5) 61-120 min'
      ELSE                                         '6) Over 120 min'
    END AS duration_bucket

  FROM `big-query-486123`.`Cyclist_Data`.`combined_trips`
);

-- Confirm the view works
SELECT COUNT(*) AS total_rows
FROM `big-query-486123`.`Cyclist_Data`.`dashboard_view`;
