import numpy as np
import matplotlib.pyplot as plt
from matplotlib import pyplot as plt, colors as clr, cm
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import pandas as pd
from datetime import datetime
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
import googlemaps
import re

path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
input_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot SPI w Drgt Stats CSV"
api_key = "***REMOVED***"
# Create a Google Maps client
gmaps = googlemaps.Client(key=api_key)
geoloc = pd.read_csv(r"C:\Users\thoma\Documents\GitHub\Drought-Research\output.csv")

def frequency_map_plot(frequency_key, spi_time):

    # Load shapefile
    directory_path = rf"C:\Users\thoma\Documents\GitHub\Drought-Research\Maps\SPI Maps - V1\Frequency Cumulative\\{spi_time}M"
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)
    counties_crs = counties.to_crs("EPSG:4326")
    frequency_df = create_frequency_dataframe(input_dir, spi_time, frequency_key)
    geoloc_call = pd.concat([frequency_df, geoloc['latitude'], geoloc['longitude']], axis=1, join='outer')
    geoloc_call['county_name'] = frequency_df['location'].apply(lambda x: re.sub(r' County$', '', x.split(',')[1]).strip())
    # Extract latitude and longitude from the latlon column
    geoloc_gdf = gpd.GeoDataFrame(geoloc_call, geometry=gpd.points_from_xy(geoloc_call['longitude'], geoloc_call['latitude']))

    # Create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the map
    counties_crs.plot(ax=ax, color='lightgray', edgecolor='black')

    # Get the minimum and maximum values
    min_freq = geoloc_gdf['frequency'].min()
    max_freq = geoloc_gdf['frequency'].max()

    # Create a list of integers from min_freq to max_freq
    frequency_range = range(min_freq, max_freq + 1)

    # Create a colormap with the same number of colors as unique values
    cmap = mcolors.ListedColormap(plt.cm.cividis(np.linspace(0, 1, len(frequency_range))))

    # Plot the map
    geoloc_gdf.plot(ax=ax, column='frequency', cmap=cmap, marker='o', vmin=min_freq-0.5, vmax=max_freq+0.5, markersize=85, edgecolor='black', linewidth=1, legend=True, legend_kwds={'ticks': frequency_range})

    # Add custom legend labels\
    plt.xlabel("Longitude", fontsize= 11)
    plt.ylabel("Latitude", fontsize= 11)
    plt.title(f'SPI Frequency Values in Missouri (SPI: {frequency_key}, SPI Time: {spi_time})', fontsize= 13)

    # Create the filename
    filename = os.path.join(directory_path, f"frequency_map_{frequency_key}_{spi_time}.jpg")

    # Save the plot
    plt.savefig(filename)
    plt.close()
    #plt.show()

def create_longest_duration_dataframe(input_dir, spi_time, drought_key):
    """
    Creates a DataFrame of Frequency values for spi_key from CSV files.

    Args:
        input_dir: The directory containing the CSV files.

    Returns:
        A Pandas DataFrame with columns for location, year, month, and SPI value.
    """

    duration_data = []
    for filename in os.listdir(input_dir):
        if filename.endswith(f"_totals_SPI_DroughtPeriod_{spi_time}_M_{drought_key}.csv"):
            file_path = os.path.join(input_dir, filename)

            # Extract location from filename (adjust as needed)
            location = filename.split("_")[0]  # Assuming location is in the first part of the filename

            # Read CSV data
            df = pd.read_csv(file_path)

            # Converts dates to be interpreted by pandas
            df['0'] = pd.to_datetime(df['0'], format='%m/%d/%Y')
            df['1'] = pd.to_datetime(df['1'], format='%m/%d/%Y')
            df['duration'] = (df['1'] - df['0']).dt.days

            # Filter for the longest duration event
            longest_duration_event = df['duration'].max()

            # Filter for the shortest duration event
            shortest_duration_event = df['duration'].min()
            
            # Append data to list
            duration_data.append({'location': location, 'SPI': drought_key, 'longest duration': longest_duration_event, 'shortest duration': shortest_duration_event})

    # Create DataFrame
    duration_df = pd.DataFrame(duration_data)

    return duration_df

def frequency_map_loop(SPI_time):
    f_key = 00

    # Iterate through possible SPI values
    while f_key != -51:
        # Call the frequency_map_plot function
        frequency_map_plot(f_key/10, SPI_time)
        f_key -= 1

print(create_longest_duration_dataframe(input_dir, '03', '-2'))
#.to_csv(r'C:\Users\thoma\Documents\GitHub\Drought-Research\Programs\output.csv', index=False)
