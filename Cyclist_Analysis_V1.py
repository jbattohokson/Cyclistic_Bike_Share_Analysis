#Load relevant libraries 
import pandas as pd
import matplotlib.pyplot as plt
import os

#Load csv files

#Upload Divvy datasets (csv files)
q1_2019 = pd.read_csv("/Users/julianbatto-hokson/Desktop/Coding/Case_Study1_Bike-Share/Divvy_Trips_2019_Q1.csv")
q1_2020 = pd.read_csv("/Users/julianbatto-hokson/Desktop/Coding/Case_Study1_Bike-Share/Divvy_Trips_2020_Q1.csv")

#WRANGLE DATA AND COMBINE INTO A SINGLE FILE

#Compare column names for each of the files
print("Columns for Q1 2019:\n", q1_2019.columns)
print("\nColumns for Q1 2020:\n", q1_2020.columns)

#Rename columns to make them consistent with q1_2020
q1_2019 = q1_2019.rename(columns={
    'trip_id': 'ride_id',
    'bikeid': 'rideable_type',
    'start_time': 'started_at',
    'end_time': 'ended_at',
    'from_station_name': 'start_station_name',
    'from_station_id': 'start_station_id',
    'to_station_name': 'end_station_name',
    'to_station_id': 'end_station_id',
    'usertype': 'member_casual'
})

#Inspect the data frames and look for incongruities
print("\nQ1 2019 Data Info:")
q1_2019.info()
print("\nQ1 2020 Data Info:")
q1_2020.info()

#Convert ride_id and rideable_type to string so that they can stack correctly
q1_2019['ride_id'] = q1_2019['ride_id'].astype(str)
q1_2019['rideable_type'] = q1_2019['rideable_type'].astype(str)

#Stack individual quarter's data frames into one big data frame
all_trips = pd.concat([q1_2019, q1_2020], ignore_index=True)

#Remove lat, long, birthyear, and gender fields as this data was dropped beginning in 2020
#The 'errors="ignore"' argument prevents an error if a column is not found
all_trips = all_trips.drop(columns=['start_lat', 'start_lng', 'end_lat', 'end_lng', 'birthyear', 'gender', 'tripduration'], errors='ignore')

#Clean up and add data to prepare for analysis

#Inspect the new table that has been created
print("\nList of column names:\n", all_trips.columns)
print("\nHow many rows are in data frame?", len(all_trips))
print("\nDimensions of the data frame:", all_trips.shape)
print("\nSee the first 6 rows of data frame:\n", all_trips.head())
print("\nSee list of columns and data types:\n")
all_trips.info()
#Statistical summary of data (mainly for numerics)
print("\nStatistical summary of data:\n", all_trips.describe())

#There are a few problems you will need to fix:
#1. In the "member_casual" column, there are two names for members ("member" and "Subscriber") and two names for casual riders ("Customer" and "casual"). You will need to consolidate that from four to two labels.
#2. The data can only be aggregated at the ride-level, which is too granular. You will want to add some additional columns of data -- such as day, month, year -- that provide additional opportunities to aggregate the data.
#3. You will want to add a calculated field for length of ride since the 2020Q1 data did not have the "tripduration" column. We will add "ride_length" to the entire data frame for consistency.
#4. There are some rides where tripduration shows up as negative, including several hundred rides where Divvy took bikes out of circulation for Quality Control reasons. You will want to delete these rides.

#In the "member_casual" column, replace "Subscriber" with "member" and "Customer" with "casual"
#Begin by discovering  how many observations fall under each usertype
print("\nValue counts for 'member_casual' column before cleaning:\n", all_trips['member_casual'].value_counts())

#Reassign to the desired values (you can go with the current 2020 labels)
all_trips['member_casual'] = all_trips['member_casual'].replace({
    'Subscriber': 'member',
    'Customer': 'casual'
})

#Check to make sure the proper number of observations were reassigned
print("\nValue counts for 'member_casual' column after cleaning:\n", all_trips['member_casual'].value_counts())

#Convert 'started_at' and 'ended_at' to datetime objects
all_trips['started_at'] = pd.to_datetime(all_trips['started_at'])
all_trips['ended_at'] = pd.to_datetime(all_trips['ended_at'])

#Add columns that list the date, month, day, and year of each ride
all_trips['date'] = all_trips['started_at'].dt.date
all_trips['month'] = all_trips['started_at'].dt.month
all_trips['day'] = all_trips['started_at'].dt.day
all_trips['year'] = all_trips['started_at'].dt.year
all_trips['day_of_week'] = all_trips['started_at'].dt.day_name()

#Add a "ride_length" calculation to all_trips (in seconds)
all_trips['ride_length'] = (all_trips['ended_at'] - all_trips['started_at']).dt.total_seconds()

#Inspect the structure of the columns
print("\nData types after adding date columns and ride_length:\n")
all_trips.info()

#Remove "bad" data
#The data frame includes entries where bikes were taken out of docks for quality checks or ride_length was negative
#Create a new version of the data frame (v2) since data is being removed
all_trips_v2 = all_trips[(all_trips['start_station_name'] != "HQ QR") & (all_trips['ride_length'] >= 0)].copy()

#Conduct descriptive analysis

#Descriptive analysis on ride_length (all figures in seconds)
print("\nDescriptive statistics for ride_length:\n", all_trips_v2['ride_length'].describe())

#Compare members and casual users
print("\nRide length statistics grouped by member_casual:\n", all_trips_v2.groupby('member_casual')['ride_length'].agg(['mean', 'median', 'max', 'min']))

#See the average ride time by each day for members vs casual users
print("\nAverage ride length by member type and day of the week:\n", all_trips_v2.groupby(['member_casual', 'day_of_week'])['ride_length'].mean())

#Order the days of the week for correct sorting for analysis
days_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
all_trips_v2['day_of_week'] = pd.Categorical(all_trips_v2['day_of_week'], categories=days_order, ordered=True)

#Run the aggregation again to see the sorted result
print("\nAverage ride length (sorted by day of week):\n", all_trips_v2.groupby(['member_casual', 'day_of_week'])['ride_length'].mean())

#Analyze ridership data by type and weekday
summary_stats = all_trips_v2.groupby(['member_casual', 'day_of_week']).agg(
    number_of_rides=('ride_id', 'count'),
    average_duration=('ride_length', 'mean')
).reset_index()

print("\nSummary of rides and duration by rider type and weekday:\n", summary_stats)

#Exports summary file for further analysis
#Create a .csv file that you will visualize elsewhere
counts = all_trips_v2.groupby(['member_casual', 'day_of_week'])['ride_length'].mean().reset_index()
counts.to_csv('avg_ride_length.csv', index=False)

#Adding ride_length in minutes since it's easier to read than seconds
all_trips_v2['ride_length_min'] = all_trips_v2['ride_length'] / 60

#Adding hour of day this might show commuter vs leisure patterns
all_trips_v2['hour'] = all_trips_v2['started_at'].dt.hour

#Make a folder for output files
output_folder = "/Users/julianbatto-hokson/Desktop/Coding/Case_Study1_Bike-Share/outputs/"
os.makedirs(output_folder, exist_ok=True)


#Extra stats to see before making charts
ride_counts = all_trips_v2.groupby('member_casual')['ride_id'].count()
member_avg_min = all_trips_v2[all_trips_v2['member_casual'] == 'member']['ride_length_min'].mean()
casual_avg_min = all_trips_v2[all_trips_v2['member_casual'] == 'casual']['ride_length_min'].mean()

print("\n--- Number of rides by rider type ---")
print(ride_counts)

print(f"\nMember avg ride length: {member_avg_min:.1f} minutes")
print(f"Casual avg ride length: {casual_avg_min:.1f} minutes")
print(f"Casual riders ride about {casual_avg_min/member_avg_min:.1f}x longer on average")

print("\n--- Number of rides by rider type and day of week ---")
print(all_trips_v2.groupby(['member_casual', 'day_of_week'])['ride_id'].count())

#VISUALIZATIONS

#Save these as PNGs to use in presentation
#Colors: blue for members, orange for casual
#Pick colors that would still be readable in grayscale
member_color = '#4472C4'
casual_color = '#ED7D31'


#Chart 1: Number of Rides by Day of Week
#This is one of the main charts the case study asks for

rides_by_day = all_trips_v2.groupby(['member_casual', 'day_of_week'])['ride_id'].count().reset_index()
rides_by_day.columns = ['member_casual', 'day_of_week', 'number_of_rides']

member_by_day = rides_by_day[rides_by_day['member_casual'] == 'member'].set_index('day_of_week').reindex(days_order)
casual_by_day = rides_by_day[rides_by_day['member_casual'] == 'casual'].set_index('day_of_week').reindex(days_order)

x = range(len(days_order))

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar([i - 0.2 for i in x], member_by_day['number_of_rides'],
       width=0.4, label='Member', color=member_color, alpha=0.85)
ax.bar([i + 0.2 for i in x], casual_by_day['number_of_rides'],
       width=0.4, label='Casual', color=casual_color, alpha=0.85)

ax.set_xticks(list(x))
ax.set_xticklabels(days_order, rotation=30, ha='right')
ax.set_title('Number of Rides by Day of Week', fontsize=14, fontweight='bold')
ax.set_xlabel('Day of Week')
ax.set_ylabel('Number of Rides')
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(output_folder + 'chart1_rides_by_day.png', dpi=150)
plt.close()
print("\nSaved chart1_rides_by_day.png")


#Chart 2: Average Ride Duration by Day of Week
#Another one the case study asks for, shows how long each group rides

duration_by_day = all_trips_v2.groupby(['member_casual', 'day_of_week'])['ride_length_min'].mean().reset_index()
duration_by_day.columns = ['member_casual', 'day_of_week', 'avg_duration']

member_dur = duration_by_day[duration_by_day['member_casual'] == 'member'].set_index('day_of_week').reindex(days_order)
casual_dur = duration_by_day[duration_by_day['member_casual'] == 'casual'].set_index('day_of_week').reindex(days_order)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(days_order, member_dur['avg_duration'], marker='o', linewidth=2,
        label='Member', color=member_color)
ax.plot(days_order, casual_dur['avg_duration'], marker='o', linewidth=2,
        label='Casual', color=casual_color)

ax.set_title('Average Ride Duration by Day of Week (minutes)', fontsize=14, fontweight='bold')
ax.set_xlabel('Day of Week')
ax.set_ylabel('Average Duration (minutes)')
ax.legend()
ax.grid(alpha=0.3)
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.savefig(output_folder + 'chart2_avg_duration_by_day.png', dpi=150)
plt.close()
print("Saved chart2_avg_duration_by_day.png")


#Chart 3: Rides by Hour of Day
#Are commuting (peaks at 8am and 5pm) vs casual riders just riding whenever

rides_by_hour = all_trips_v2.groupby(['member_casual', 'hour'])['ride_id'].count().reset_index()
rides_by_hour.columns = ['member_casual', 'hour', 'number_of_rides']

member_hourly = rides_by_hour[rides_by_hour['member_casual'] == 'member']
casual_hourly = rides_by_hour[rides_by_hour['member_casual'] == 'casual']

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(member_hourly['hour'], member_hourly['number_of_rides'], marker='o',
        linewidth=2, label='Member', color=member_color)
ax.plot(casual_hourly['hour'], casual_hourly['number_of_rides'], marker='o',
        linewidth=2, label='Casual', color=casual_color)

ax.set_title('Number of Rides by Hour of Day', fontsize=14, fontweight='bold')
ax.set_xlabel('Hour of Day (0 = midnight)')
ax.set_ylabel('Number of Rides')
ax.set_xticks(range(0, 24))
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(output_folder + 'chart3_rides_by_hour.png', dpi=150)
plt.close()
print("Saved chart3_rides_by_hour.png")


#Chart 4: Monthly Ride Volume
#Only Jan-Mar since this is Q1 data would be interesting to see a full year

rides_by_month = all_trips_v2.groupby(['member_casual', 'month'])['ride_id'].count().reset_index()
rides_by_month.columns = ['member_casual', 'month', 'number_of_rides']

member_monthly = rides_by_month[rides_by_month['member_casual'] == 'member']
casual_monthly = rides_by_month[rides_by_month['member_casual'] == 'casual']

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar([m - 0.2 for m in member_monthly['month']], member_monthly['number_of_rides'],
       width=0.4, label='Member', color=member_color, alpha=0.85)
ax.bar([m + 0.2 for m in casual_monthly['month']], casual_monthly['number_of_rides'],
       width=0.4, label='Casual', color=casual_color, alpha=0.85)

ax.set_xticks([1, 2, 3])
ax.set_xticklabels(['January', 'February', 'March'])
ax.set_title('Monthly Ride Volume - Q1 Only', fontsize=14, fontweight='bold')
ax.set_xlabel('Month')
ax.set_ylabel('Number of Rides')
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(output_folder + 'chart4_rides_by_month.png', dpi=150)
plt.close()
print("Saved chart4_rides_by_month.png")


#Chart 5: Top 10 Start Stations for Casual Riders
#Casual riders are starting their trips could help target ads or promotions

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
plt.savefig(output_folder + 'chart5_top_stations_casual.png', dpi=150)
plt.close()
print("Saved chart5_top_stations_casual.png")


#EXPORT CLEANED DATA

#Saving the full cleaned dataset to use in Tableau later
#Only exports the avg_ride_length summary

all_trips_v2.to_csv(output_folder + 'all_trips_clean.csv', index=False)
print("\nSaved all_trips_clean.csv")

#Summary by rider type and day, good for Tableau
summary_by_day = all_trips_v2.groupby(['member_casual', 'day_of_week']).agg(
    number_of_rides=('ride_id', 'count'),
    avg_ride_length_min=('ride_length_min', 'mean')
).reset_index()
summary_by_day.to_csv(output_folder + 'summary_by_day.csv', index=False)
print("Saved summary_by_day.csv")

rides_by_month.to_csv(output_folder + 'summary_by_month.csv', index=False)
print("Saved summary_by_month.csv")

rides_by_hour.to_csv(output_folder + 'summary_by_hour.csv', index=False)
print("Saved summary_by_hour.csv")



#KEY FINDINGS

#Summarizing what was found to answer the business question:
#"How do annual members and casual riders use Cyclistic bikes differently?"
member_pct = ride_counts['member'] / ride_counts.sum() * 100
casual_pct = ride_counts['casual'] / ride_counts.sum() * 100

print("\n========================================")
print("KEY FINDINGS")
print(f"""
1. Members make up {member_pct:.0f}% of total rides but casual riders take 
   much longer trips on average ({casual_avg_min:.0f} min vs {member_avg_min:.0f} min).
   That's about {casual_avg_min/member_avg_min:.1f}x longer per ride.

2. Members ride mostly on weekdays -- this looks like commuting behavior.
   Casual riders ride more on weekends which points to leisure use.

3. Members have clear peaks around 8am and 5pm (rush hour).
   Casual riders are more spread out through the day.

4. March has the highest ride volume for both groups, probably because
   the weather is getting better coming out of winter.

   Note: this is only Q1 data so I can't see the full seasonal picture.
   I'd want to look at full-year data before drawing strong conclusions.
""")

print("========================================")
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






