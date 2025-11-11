import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.interpolate import interp1d
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
import os

# --- Configuration ---
# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# --- Function to find the latest weather data file ---
def find_latest_weather_file(directory):
    """Finds the most recent 'weather_data_YYYY-MM-DD.csv' file."""
    weather_files = [f for f in os.listdir(directory) if f.startswith('weather_data_') and f.endswith('.csv')]
    if not weather_files:
        return None
    # Sort files by date, most recent first
    weather_files.sort(reverse=True)
    return weather_files[0]

# Define paths relative to the script's location
SPI_THRESHOLDS_PATH = os.path.join(script_dir, 'spi_to_rainfall_conversion.csv')
latest_weather_file = find_latest_weather_file(script_dir)
if not latest_weather_file:
    print("CRITICAL ERROR: No 'weather_data_*.csv' file found in the script directory.")
    exit()
WEATHER_DATA_PATH = os.path.join(script_dir, latest_weather_file)
print(f"Using weather data file: {WEATHER_DATA_PATH}")

STATION_LOCATIONS_PATH = os.path.join(script_dir, 'output.csv')
COUNTY_SHAPEFILE_PATH = os.path.join(script_dir, 'MO_County_Boundaries.shp')
OUTPUT_DIR = os.path.join(script_dir, 'Maps', 'SPI_Maps') # Directory to save maps

# --- 1. Load Data ---
print("Loading data...")
spi_df = pd.read_csv(SPI_THRESHOLDS_PATH) 
weather_df = pd.read_csv(WEATHER_DATA_PATH)
print("Loading station locations...")
try:
    locations_df = pd.read_csv(STATION_LOCATIONS_PATH)
except Exception as e:
    print(f"CRITICAL ERROR: Could not load {STATION_LOCATIONS_PATH}.")
    print(f"Please create this file with 'Station Name', 'Latitude', and 'Longitude' columns.")
    print(f"Error: {e}")
    exit()

# --- 2. SPI Calculation Function ---
def calculate_spi(row, spi_subset):
    location = row['Station Name']
    rainfall = row['Total Precipitation (in)']
    loc_thresholds = spi_subset[spi_subset['Location'] == location].sort_values('SPI_Value')
    
    if loc_thresholds.empty:
        print(f"Warning: No SPI thresholds found for {location}. Skipping.")
        return np.nan
    
    # Use interpolation to find exact SPI from rainfall
    try:
        f_interp = interp1d(loc_thresholds['Rainfall_Threshold_in'], loc_thresholds['SPI_Value'], 
                            kind='linear', fill_value="extrapolate")
        return float(f_interp(rainfall))
    except Exception as e:
        print(f"Error interpolating for {location}: {e}")
        return np.nan

# --- 3. Map Plotting Function ---
def plot_spi_map(gdf, plot_date, timescale, output_path):
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    try:
        counties = gpd.read_file(COUNTY_SHAPEFILE_PATH)
        counties = counties.to_crs(epsg=4326)
        counties.plot(ax=ax, facecolor='white', edgecolor='black', linewidth=1.2, zorder=1)
    except Exception as e:
        print(f"Warning: Could not load county shapefile: {e}")
        ax.add_feature(cfeature.STATES, linewidth=1.5, edgecolor='black')

    # Define SPI colormap and bins
    spi_bins = [-np.inf, -2.0, -1.6, -1.3, -0.8, -0.5, 0.5, 0.8, 1.3, 1.6, 2.0, np.inf]
    spi_colors = [
        '#730000', '#E60000', '#E69800', '#FED37F', '#FEFE00', 
        '#FFFFFF', '#AAF596', '#4CE600', '#38A800', '#145A00', '#002673'
    ]
    cmap = ListedColormap(spi_colors)
    norm = BoundaryNorm(spi_bins, cmap.N)

    # Use the 'Longitude' and 'Latitude' columns from the merged GeoDataFrame
    ax.scatter(gdf['Longitude'], gdf['Latitude'], c=gdf['CALCULATED_SPI'], 
               cmap=cmap, norm=norm, s=150, edgecolors='black', zorder=3, transform=ccrs.PlateCarree())

    # Legend
    legend_elements = [
        Patch(facecolor=spi_colors[i], edgecolor='k', label=label) for i, label in enumerate([
            '<= D4 Exceptional Drought)', 'D3 Extreme Drought', 'D2 Severe Drought',
            'D1 Moderate Drought', 'D0 Abnormally Dry', 'Near Normal',
            'W0 Abnormally Wet', 'W1 Moderately Wet', 'W2 Severely Wet',
            'W3 Extremely Wet', 'W4 Exceptionally Wet'
        ])
    ]

    ax.legend(handles=legend_elements, title="SPI Categories", fontsize=10, title_fontsize=11, loc='upper left', bbox_to_anchor=(1, 1))
    ax.set_title(f"{timescale}-Month SPI - {plot_date}", fontsize=16)
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Map saved to {output_path}")

# --- 4. Main Loop for Generating Maps ---
# Define periods and corresponding timescales (adjust as needed based on your data)
periods_to_process = {
    'Past Month': {'timescale': 1},
    'Past 3 Months': {'timescale': 3},
    'Past 6 Months': {'timescale': 6},
    'Past 12 Months': {'timescale': 12},
}

for period_name, params in periods_to_process.items():
    print(f"Processing map for {period_name}...")
    timescale = params['timescale']
    
    # Dynamically get the month and year from the data
    period_data = weather_df[weather_df['Period'] == period_name]
    if period_data.empty:
        print(f"No data for '{period_name}' in the weather file. Skipping.")
        continue
    end_date = pd.to_datetime(period_data['End Date'].iloc[0])
    target_month = end_date.strftime('%B')
    target_year = end_date.year
    
    spi_subset = spi_df[(spi_df['Timescale_Months'] == timescale) & (spi_df['Month'] == target_month)]
    weather_subset = weather_df[weather_df['Period'] == period_name].copy()
    
    if weather_subset.empty:
        print(f"No weather data found for period: {period_name}")
        continue
    
    # --- NEW: Combine weather data with locations based on order ---
    # Sort the weather data by station name to ensure it matches the order of the locations file.
    weather_subset = weather_subset.sort_values(by='Station Name').reset_index(drop=True)
    
    # Make sure the number of stations matches
    if len(weather_subset) != len(locations_df):
        print(f"Warning: Mismatch in station count for '{period_name}'. Weather data has {len(weather_subset)} stations, locations file has {len(locations_df)}. Skipping map.")
        continue

    # Concatenate the dataframes side-by-side
    weather_subset_geocoded = pd.concat([weather_subset, locations_df], axis=1)
    weather_subset_geocoded['CALCULATED_SPI'] = weather_subset_geocoded.apply(lambda row: calculate_spi(row, spi_subset), axis=1)

    # Filter out stations with missing coordinates or SPI values
    weather_subset_geocoded = weather_subset_geocoded.dropna(subset=['Latitude', 'Longitude', 'CALCULATED_SPI'])

    if weather_subset_geocoded.empty:
        print(f"No valid station data for map generation for {period_name}.")
        continue
    
    # --- NEW: Create GeoDataFrame using the merged columns ---
    gdf = gpd.GeoDataFrame(
        weather_subset_geocoded, 
        geometry=gpd.points_from_xy(weather_subset_geocoded.Longitude, weather_subset_geocoded.Latitude), 
        crs="EPSG:4326"
    )
    
    output_filename = os.path.join(OUTPUT_DIR, f"Missouri_SPI_{timescale}Month_{target_month}{target_year}.png")
    plot_spi_map(gdf, f"{target_month} {target_year}", timescale, output_filename)

print("All maps generated.")