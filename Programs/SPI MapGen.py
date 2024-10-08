import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import contextily as ctx  # Optional for basemap
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
from geopy.geocoders import Nominatim
import googlemaps



path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
input_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot SPI w Drgt Stats CSV"
api_key = "***REMOVED***"
# Create a Google Maps client
gmaps = googlemaps.Client(key=api_key)


def spi_map_plot():

    # Load shapefile
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)
    counties_crs = counties.to_crs("EPSG:3857")
    test_df = create_spi_dataframe(input_dir, '03', '07/01/2001')
    geoloc = geocode_locations(test_df)
    # Extract latitude and longitude from the latlon column
    geoloc_gdf = gpd.GeoDataFrame(geoloc, geometry=gpd.points_from_xy(geoloc['longitude'], geoloc['latitude']))
    
    # Join DataFrames based on a common identifier (e.g., location name)
    merged_df = counties_crs.join(geoloc_gdf.set_index('location'), on='COUNTYNAME', lsuffix='_county', rsuffix='_geoloc')

    # Plot the map
    merged_df.plot(column='spi', cmap='YlGnBu', legend=True)
    plt.title('SPI Values in Missouri')
    plt.show()


def geocode_locations(df):
    """
    Geocodes locations in a DataFrame using Nominatim.

    Args:
        df: The DataFrame containing location names.

    Returns:
        A DataFrame with added latitude and longitude columns.
    """

    def geocode_location(location):
        try:
            geocode_result = gmaps.geocode(location)
            if geocode_result:
                latitude = geocode_result[0]['geometry']['location']['lat']
                longitude = geocode_result[0]['geometry']['location']['lng']
                return latitude, longitude
            else:
                print(f"Geocoding failed for {location}")
                return None, None
        except Exception as e:
            print(f"Error geocoding {location}: {e}")
            return None, None

    df['latlon'] = df['location'].apply(geocode_location)
    # Extract latitude and longitude from the latlon column
    df[['latitude', 'longitude']] = pd.DataFrame(df['latlon'].tolist(), index=df.index)

    return df

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

spi_map_plot()