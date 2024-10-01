import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import contextily as ctx  # Optional for basemap
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable

path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
input_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot SPI w Drgt Stats CSV"

def spi_map_plot():

    # Load shapefile
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)

    # Create GeoDataFrame from your data
    df = create_spi_dataframe(input_dir, '03', '12/01/2000')

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']))

    # Join with shapefile (assuming a common column like 'county_name')
    merged_df = counties.join(gdf.set_index('location'), on='name')

    # Create choropleth map
    merged_df.plot(column='value', cmap='YlGnBu', legend=True)
    plt.title('Distribution of Values in Missouri')
    plt.show()

def create_spi_dataframe(input_dir, spi_time, month_key):
    """
    Creates a DataFrame of SPI values for January 2000 from CSV files.

    Args:
        input_dir: The directory containing the CSV files.

    Returns:
        A Pandas DataFrame with columns for location, year, month, and SPI value.
    """
    spi_row = 'none'

    if spi_time == '01':
        spi_row = '1'
    elif spi_time == '03':
        spi_row = '2'
    elif spi_time == '06':
        spi_row = '3'
    else:
        spi_row = '2'

    spi_data = []
    for filename in os.listdir(input_dir):
        if filename.endswith("SPI_M_01_03_06_12.csv"):
            file_path = os.path.join(input_dir, filename)

            # Extract location from filename (adjust as needed)
            location = filename.split("_")[0]  # Assuming location is in the first part of the filename

            # Read CSV data
            df = pd.read_csv(file_path)
           
            # Filter for January 2000 data
            january_2000_data = df[(df['0'] == month_key) & (df[spi_row].notnull())]

            # Extract SPI value
            spi_value = january_2000_data[spi_row].iloc[0]

            # Append data to list
            spi_data.append({'location': location, 'spi': spi_value})

    # Create DataFrame
    spi_df = pd.DataFrame(spi_data)

    return spi_df
