import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import pandas as pd
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
import googlemaps
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
    
    # Group the DataFrame by location and calculate the average duration
    cumulative_durations = duration_df.groupby('location')['start_date'].mean().reset_index()

    return cumulative_durations



def seasonality_table_loop(SPI_time):
    spi_key = 00

    try:
        # Iterate through possible SPI values
        while spi_key != -51:
            # Call the frequency_map_plot function
            dfcsv = create_seasonality_dataframe(input_dir, SPI_time, spi_key/10)
            spi_key -= 1
            dfcsv.to_csv(rf'C:\Users\thoma\Documents\GitHub\Drought-Research\Tabular Data\Raw Seasonality\{SPI_time}M\{spi_key/10}_{SPI_time}M_raw_seasonality.csv', index=False)
    except:
        return None

print(create_seasonality_dataframe(input_dir, '03', -0.3))

#seasonality_table_loop('01')
#seasonality_table_loop('03')
#seasonality_table_loop('06')
#seasonality_table_loop('12')