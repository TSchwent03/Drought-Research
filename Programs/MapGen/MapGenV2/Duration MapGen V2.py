import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import pandas as pd
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
import re

path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
input_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot SPI w Drgt Stats CSV"
geoloc = pd.read_csv(r"C:\Users\thoma\Documents\GitHub\Drought-Research\output.csv")

def create_duration_dataframe(input_dir, spi_time, drought_threshold):
    """
    Creates a DataFrame of drought durations for a given SPI time scale and threshold.

    Args:
        input_dir: The directory containing the CSV files.
        spi_time: The SPI time scale (e.g., '01', '03', '06', '12').
        drought_threshold: The SPI threshold defining a drought event.

    Returns:
        A Pandas DataFrame with columns for location, SPI threshold, start date, end date, and duration.
    """

    duration_data = []
    for filename in os.listdir(input_dir):
        if filename.endswith(f"SPI_M_01_03_06_12.csv"):
            file_path = os.path.join(input_dir, filename)

            # Extract location from filename
            location = filename.split("_")[0]

            # Read CSV data
            df = pd.read_csv(file_path)

            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['0'], format='%m/%d/%Y')

            # Select the appropriate SPI column
            spi_row = 'none'
            if spi_time == '01':
                spi_row = '1'
            elif spi_time == '03':
                spi_row = '2'
            elif spi_time == '06':
                spi_row = '3'
            elif spi_time == '12':
                spi_row = '4'

            # Skip the first spi_key - 1 rows
            df = df.iloc[int(spi_time) - 1:]

            # Identify drought events and calculate durations
            drought_start = None
            for index, row in df.iterrows():
                if row[spi_row] <= drought_threshold:
                    if drought_start is None:
                        drought_start = index
                else:
                    if drought_start is not None:
                        drought_end = index
                        duration = drought_end - drought_start
                        duration_data.append({'location': location, 'SPI': drought_threshold, 'start_date': drought_start, 'end_date': drought_end, 'duration': duration})
                        drought_start = None

    # Create DataFrame
    duration_df = pd.DataFrame(duration_data)

    # Group the DataFrame by location and calculate the average duration
    cumulative_durations = duration_df.groupby('location')['duration'].sum().reset_index()

    # Calculate the total number of months in the observation period.
    # The full period is Jan 2000 - May 2024 (293 months).
    # We subtract (spi_time - 1) because the first N-1 SPI values are undefined for an N-month SPI.
    total_observation_months = 293 - (int(spi_time) - 1)

    # Calculate the duration as a percentage of the total observation time
    cumulative_durations['duration'] = (cumulative_durations['duration'] / total_observation_months) * 100

    return cumulative_durations

def duration_map_plot(spi_key, spi_time):

    # Load shapefile
    directory_path = rf"C:\Users\thoma\Documents\GitHub\Drought-Research\Maps\SPI Maps - V2\Frequency\\{spi_time}M"
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)
    counties_crs = counties.to_crs("EPSG:4326")
    duration_df = create_duration_dataframe(input_dir, spi_time, spi_key)
    geoloc_call = pd.concat([duration_df, geoloc['latitude'], geoloc['longitude']], axis=1, join='outer')
    geoloc_call['county_name'] = duration_df['location'].apply(lambda x: re.sub(r' County$', '', x.split(',')[0]).strip())
    # Extract latitude and longitude from the latlon column
    geoloc_gdf = gpd.GeoDataFrame(geoloc_call, geometry=gpd.points_from_xy(geoloc_call['longitude'], geoloc_call['latitude']))

    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8, 5))

    # Plot the map
    counties_crs.plot(ax=ax, color='lightgray', edgecolor='black')
    # Plots Graduated Color Mapping
    geoloc_gdf.plot(ax=ax ,column='duration', cmap='cividis', legend=True, markersize=77, edgecolor='black', linewidth=1)

    # Add custom legend labels
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f'{spi_key} SPI Drought Frequency (%) | {spi_time} Month SPI', fontsize= 13)

    # Create the filename
    filename = os.path.join(directory_path, f"spi_map_{spi_key}_{spi_time}.jpg")

    # Save the plot
    plt.savefig(filename)
    plt.close()
    #plt.show()

def duration_map_loop(SPI_time):
    spi_key = 00

    try:
        # Iterate through possible SPI values
        while spi_key != -51:
            # Call the frequency_map_plot function
            duration_map_plot(spi_key/10, SPI_time)
            spi_key -= 1
    except:
        return None

def duration_table_loop(SPI_time):
    spi_key = 00

    try:
        # Iterate through possible SPI values
        while spi_key != -51:
            # Call the frequency_map_plot function
            dfcsv = create_duration_dataframe(input_dir, SPI_time, spi_key/10)
            dfcsv.to_csv(rf'C:\Users\thoma\Documents\GitHub\Drought-Research\Tabular Data\Duration\{SPI_time}M\{spi_key/10}_{SPI_time}M_events.csv', index=False)
            spi_key -= 1
    except:
        return None
    
duration_map_loop('12')
#duration_map_plot(-0.5, '01')