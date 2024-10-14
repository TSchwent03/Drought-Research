import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import contextily as ctx  # Optional for basemap
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

def spi_map_plot(month, spi_time):

    # Load shapefile
    directory_path = rf"C:\Users\thoma\Documents\GitHub\Drought-Research\Maps\SPI Maps - V1\Categorical\\{month}"
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)
    counties_crs = counties.to_crs("EPSG:4326")
    spi_df = create_spi_dataframe(input_dir, spi_time, month)
    geoloc_call = pd.concat([spi_df, geoloc['latitude'], geoloc['longitude']], axis=1, join='outer')
    geoloc_call['county_name'] = spi_df['location'].apply(lambda x: re.sub(r' County$', '', x.split(',')[1]).strip())
    # Extract latitude and longitude from the latlon column
    geoloc_gdf = gpd.GeoDataFrame(geoloc_call, geometry=gpd.points_from_xy(geoloc_call['longitude'], geoloc_call['latitude']))

    # Create figure and axes
    fig, ax = plt.subplots()

    # Plot the map
    counties_crs.plot(ax=ax, color='lightgray', edgecolor='black')
    # Plots Graduated Color Mapping
    #geoloc_gdf.plot(ax=ax ,column='spi', cmap='BrBG', vmin=-2, vmax=2, legend=True, markersize=75, edgecolor='black', linewidth=1)

    # Plots Categorical Color Mapping
    # Define thresholds and corresponding hex codes
    ranges = [(-np.inf, -2), (-1.99, -1.6), (-1.59, -1.3), (-1.29, -0.8), (-0.79, -0.5), (-0.49, 0.49), (0.5, 0.79), (0.8, 1.29), (1.3, 1.59), (1.6, 1.99), (2, np.inf)]
    hex_codes = ['#730000', '#E60000', '#E69800', '#FED37F', '#FEFE00', '#FFFFFF', '#AAF596', '#4CE600', '#38A800', '#145A00', '#002673']
    labels = ['D4', 'D3', 'D2', 'D1', 'D0', 'N', 'W0', 'W1', 'W2', 'W3', 'W4']
    # Create a ListedColormap from the ranges, hex codes, and labels
    cmap = mcolors.ListedColormap(hex_codes, N=len(ranges))
    # Plot the map with the custom colormap
    geoloc_gdf.plot(ax=ax, column='spi', cmap=cmap, vmin=-2, vmax=2, markersize=75, edgecolor='black', linewidth=1)
    # Add custom legend labels
    plt.legend(labels = labels, loc='upper left', bbox_to_anchor=(1.05, 1))
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f'SPI Values in Missouri (Month: {month}, SPI Time: {spi_time})', fontsize= 11)

    # Replace forward slashes with hyphens in the month
    month_formatted = re.sub('/', '-', month)

    # Create the filename
    filename = os.path.join(directory_path, f"spi_map_{month_formatted}_{spi_time}.jpg")

    # Save the plot
    #plt.savefig(filename)
    #plt.close()
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
    elif spi_time == '12':
        spi_row = '4'

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

def spi_map_loop(SPI_time):
    # Create a date range from 01/01/2000 to 05/01/2024
    start_date = pd.to_datetime('01/01/2000')
    end_date = pd.to_datetime('05/01/2024')

    # Iterate through the date range
    for current_date in pd.date_range(start_date, end_date, freq='MS'):
        month = current_date.month
        year = current_date.year
        spi_time = 1  # Adjust SPI time as needed
        month_key = f"{month:02d}/01/{year}"
        # Call the spi_map_plot function
        spi_map_plot(month_key, SPI_time)

#Geocode Locations
#locations_df = create_spi_dataframe(input_dir, '01', '01/01/2000')
#geoloc = geocode_locations(locations_df)
#geoloc_out = pd.concat([geoloc['latitude'], geoloc['longitude']], axis = 1, join = 'outer')
#geoloc_out.to_csv(r'C:\Users\thoma\Documents\GitHub\Drought-Research\output.csv', index=False)

spi_map_plot('01/01/2024', '12')