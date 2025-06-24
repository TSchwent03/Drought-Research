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

def create_seasonality_dataframe(input_dir, spi_time, drought_threshold):
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
                        drought_start = row['date']
                else:
                    if drought_start is not None:
                        drought_end = row['date']
                        duration = drought_end - drought_start
                        duration_data.append({'location': location, 'SPI': drought_threshold, 'start_date': drought_start, 'end_date': drought_end, 'duration': duration})
                        drought_start = None

    # Create DataFrame
    duration_df = pd.DataFrame(duration_data)

    # Extract the month from the 'start_date' column
    duration_df['start_month'] = duration_df['start_date'].dt.month
    duration_df['end_month'] = duration_df['end_date'].dt.month

    return duration_df



def seasonality_table_loop(SPI_time):
    spi_key = 00

    try:
        # Iterate through possible SPI values
        while spi_key != -51:
            # Call the frequency_map_plot function
            dfcsv = determine_most_frequent_season_by_location(create_seasonality_dataframe(input_dir, SPI_time, spi_key/10))
            dfcsv.to_csv(rf'C:\Users\thoma\Documents\GitHub\Drought-Research\Tabular Data\Relief Seasonality\{SPI_time}M\{spi_key/10}_{SPI_time}M_seasonality.csv', index=False)
            spi_key -= 1     
    except:
        return None

def determine_most_frequent_season_by_location(df):
    """
    Determines the most frequent season of drought onset for each location.

    Args:
        df: A DataFrame with 'location' and 'start_date' columns.

    Returns:
        A DataFrame with 'location' and 'most_frequent_season' columns.
    """

    def season_frequency(dates):
        season_counts = {'Winter': 0, 'Spring': 0, 'Summer': 0, 'Fall': 0}
        for date in dates:
            month = date.month
            if month in [12, 1, 2]:
                season_counts['Winter'] += 1
            elif month in [3, 4, 5]:
                season_counts['Spring'] += 1
            elif month in [6, 7, 8]:
                season_counts['Summer'] += 1
            else:
                season_counts['Fall'] += 1

        return season_counts
    
    def check_row_max_equality(row):
        """
        Checks if any columns in a given row of a DataFrame have the same maximum value.

        Args:
            row: A pandas Series representing a row of the DataFrame.

        Returns:
            True if any columns have the same maximum value, False otherwise.
        """

        max_value = row[1:5].max()  # Consider columns 1 to 4 (inclusive)
        return (row[1:5] == max_value).sum() > 1


    # Group the DataFrame by location and apply the function
    seasonal_counts_df = df.groupby('location')['start_date'].apply(season_frequency).apply(pd.Series).reset_index()
    df_pivoted = seasonal_counts_df.pivot_table(index='location', columns='level_1', values=0, aggfunc='sum').reset_index()
    df_pivoted['most_frequent_season'] = df_pivoted[['Winter', 'Spring', 'Summer', 'Fall']].idxmax(axis=1)    
    # Apply the function to each row
    df_pivoted['has_equal_max_columns'] = df_pivoted.apply(check_row_max_equality, axis=1)
    # Assign 'Tie' category to rows with multiple maximum values
    df_pivoted['most_frequent_season'] = df_pivoted.apply(
        lambda row: 'Tie' if row['has_equal_max_columns'] else row['most_frequent_season'], axis=1)

    return df_pivoted

def seasonality_map_plot(spi_key, spi_time):

    # Load shapefile
    directory_path = rf"C:\Users\thoma\Documents\GitHub\Drought-Research\Maps\SPI Maps - V2\Onset Seasonality\\{spi_time}M"
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)
    counties_crs = counties.to_crs("EPSG:4326")
    seasonality_df = determine_most_frequent_season_by_location(create_seasonality_dataframe(input_dir, spi_time, spi_key))
    geoloc_call = pd.concat([seasonality_df, geoloc['latitude'], geoloc['longitude']], axis=1, join='outer')
    geoloc_call['county_name'] = seasonality_df['location'].apply(lambda x: re.sub(r' County$', '', x.split(',')[1]).strip())
    # Extract latitude and longitude from the latlon column
    geoloc_gdf = gpd.GeoDataFrame(geoloc_call, geometry=gpd.points_from_xy(geoloc_call['longitude'], geoloc_call['latitude']))

    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8.5, 5))

    # Plot the map
    counties_crs.plot(ax=ax, color='lightgrey', edgecolor='black')

    season_to_int = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3, 'Tie': 4}
    geoloc_gdf['season_int'] = geoloc_gdf['most_frequent_season'].replace(season_to_int)


    # Plots Categorical Color Mapping
    colors = ['#4FA5ED', '#30D91C', '#F7DF1B', '#C62A03', '#6F6F6F']
    cmap = mcolors.ListedColormap(colors)

    # Plot the map with the custom colormap
    geoloc_gdf.plot(ax=ax, column='season_int', marker='o', cmap=cmap, markersize=77, edgecolor='black', linewidth=1)
    legend_elements = [Patch(edgecolor='black', label='Winter', facecolor='#4FA5ED'), 
                       Patch(edgecolor='black', label='Spring', facecolor='#30D91C'), 
                       Patch(edgecolor='black', label='Summer', facecolor='#F7DF1B'), 
                       Patch(edgecolor='black', label='Fall', facecolor='#C62A03'), 
                       Patch(edgecolor='black', label='Tie', facecolor='#6F6F6F') 
                      ]


    ax.legend(handles=legend_elements, bbox_to_anchor=(1, 1), loc='upper left')

    # Add custom legend labels
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f'Drought Onset Seasonality (Spi Key: {spi_key} , SPI Time: {spi_time})', fontsize= 13)

    # Create the filename
    filename = os.path.join(directory_path, f"seasonality_map_{spi_key}_{spi_time}.jpg")

    # Save the plot
    plt.savefig(filename)
    plt.close()
    #print(seasonality_df)
    #print(geoloc_gdf)
    #plt.show()

def seasonality_map_loop(SPI_time):
    f_key = 00

    try:
        # Iterate through possible SPI values
        while f_key != -51:
            # Call the frequency_map_plot function
            seasonality_map_plot(f_key/10, SPI_time)
            f_key -= 1
    except:
        return None

#seasonality_df = determine_most_frequent_season_by_location(create_seasonality_dataframe(input_dir, '03', -0.3))

#print(seasonality_df)

#seasonality_map_plot(-1.0, '01')
#print(determine_most_frequent_season_by_location(create_seasonality_dataframe(input_dir, '01', -1.0)))
#print(determine_most_frequent_season_by_location(create_seasonality_dataframe(input_dir, '01', -10/10)))
seasonality_map_loop('01')
seasonality_map_loop('03')
seasonality_map_loop('06')
seasonality_map_loop('12')