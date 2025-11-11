import cdsapi
import xarray as xr
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
from pathlib import Path
import re
from datetime import datetime
import calendar

# --- Configuration ---
# Use Pathlib for robust, OS-agnostic paths
BASE_DIR = Path(__file__).resolve().parent # Use the script's directory as the base
OUTPUT_DIR = BASE_DIR / "Forecast_Products"
MAP_OUTPUT_DIR = OUTPUT_DIR / "SPI_Maps"
METEOGRAM_OUTPUT_DIR = OUTPUT_DIR / "Station_Meteograms"

# Input File Paths
SPI_THRESHOLDS_PATH = BASE_DIR / 'spi_to_rainfall_conversion.csv'
STATION_LOCATIONS_PATH = BASE_DIR / 'output.csv'
COUNTY_SHAPEFILE_PATH = BASE_DIR / 'MO_County_Boundaries.shp'

# Forecast Settings (SET THESE)
FORECAST_YEAR = '2025'
FORECAST_MONTH = '11' # Use '11' for November
FORECAST_AREA = [41, -96, 35, -88] # North, West, South, East (Missouri Box)
NETCDF_FILENAME = f"seas5_fc_{FORECAST_YEAR}_{FORECAST_MONTH}.nc"
NETCDF_FULL_PATH = OUTPUT_DIR / NETCDF_FILENAME

# --- 1. CDS API Data Download ---
def download_seas_data():
    """
    Downloads ECMWF SEAS5 ensemble forecast data using cdsapi.
    """
    if NETCDF_FULL_PATH.exists():
        print(f"Forecast file already exists: {NETCDF_FULL_PATH}")
        return

    print("Downloading SEAS5 forecast data from CDS...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    client = cdsapi.Client()
    try:
        client.retrieve(
            "seasonal-monthly-single-levels",
            {
                "originating_centre": "ecmwf",
                "system": "51",
                "variable": ["total_precipitation"], # Use 'total_precipitation' (tpr)
                "year": [FORECAST_YEAR],
                "month": [FORECAST_MONTH],
                "leadtime_month": ["1", "2", "3", "4", "5", "6"],
                "format": "netcdf",
                "product_type": ["ensemble_members"],
                "area": FORECAST_AREA,
            },
            NETCDF_FULL_PATH
        )
        print(f"Download complete: {NETCDF_FULL_PATH}")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to download data from CDS.")
        print(f"Error: {e}")
        if NETCDF_FULL_PATH.exists():
            os.remove(NETCDF_FULL_PATH) # Remove partial file
        exit()

# --- 2. Create SPI Interpolation Functions ---
def create_spi_interpolators(spi_df):
    """
    Loads 1-month SPI thresholds and creates an interpolation function
    (rainfall -> SPI) for each station and month.
    """
    print("Creating SPI interpolation functions...")
    interpolators = {}
    
    # Filter for 1-month SPI, as we are forecasting month-by-month
    spi_1mo = spi_df[spi_df['Timescale_Months'] == 1]
    
    for location in spi_1mo['Location'].unique():
        interpolators[location] = {}
        for month in spi_1mo['Month'].unique():
            loc_month_data = spi_1mo[(spi_1mo['Location'] == location) & (spi_1mo['Month'] == month)].sort_values('SPI_Value')
            if not loc_month_data.empty:
                # Create the function: x=Rainfall, y=SPI
                interpolators[location][month] = interp1d(
                    loc_month_data['Rainfall_Threshold_in'],
                    loc_month_data['SPI_Value'],
                    kind='linear',
                    fill_value="extrapolate" # Extrapolate for extreme forecast values
                )
    print("SPI interpolators created.")
    return interpolators

# --- 3. Generate SPI Forecasts from NetCDF ---
def generate_spi_forecasts(station_df, interpolators):
    """
    Processes the downloaded NetCDF. For each station, lead month, and member,
    it converts the forecasted rainfall (in) to a forecasted SPI.
    """
    print(f"Opening NetCDF file: {NETCDF_FULL_PATH}")
    try:
        ds = xr.open_dataset(NETCDF_FULL_PATH)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not open {NETCDF_FULL_PATH}. Was download successful?")
        print(f"Error: {e}")
        exit()

    # Get the calendar month names for each lead time
    # This is crucial for matching with the correct interpolator
    print(ds)
    start_month = int(FORECAST_MONTH)
    month_names = [calendar.month_name[(start_month + i - 1) % 12 + 1] for i in ds.forecastMonth.values]
    
    all_spi_forecasts = []

    print("Processing forecasts for all stations...")
    for _, station in station_df.iterrows():
        station_name = station['Station Name']
        lat = station['Latitude']
        lon = station['Longitude']
        
        if station_name not in interpolators:
            print(f"Warning: No interpolator for {station_name}. Skipping.")
            continue

        # Extract the time series for this station from the xarray dataset
        station_ds = ds.sel(latitude=lat, longitude=lon, method='nearest')
        for i, lead_month in enumerate(ds.forecastMonth.values):
            month_name = month_names[i] # e.g., 'November'
            
            if month_name not in interpolators[station_name]:
                print(f"Warning: No 1-mo SPI data for {station_name} in {month_name}. Skipping.")
                continue

            # Get rainfall rate (m/s) for all ensemble members
            # 'tpr' is the typical variable name for total precipitation rate
            precip_rate_members = station_ds['tprate'].sel(forecastMonth=lead_month)
            
            # Convert m/s to total inches for the month
            days_in_month = calendar.monthrange(int(FORECAST_YEAR), (start_month + i - 1) % 12 + 1)[1]
            seconds_in_month = days_in_month * 24 * 60 * 60
            
            # Convert from rate (m/s) to total accumulation (m)
            precip_m_members = precip_rate_members * seconds_in_month
            # Convert meters to inches (1 meter = 39.3701 inches)
            precip_in_members = precip_m_members * 39.3701
            
            # Get the correct interpolation function
            f_interp = interpolators[station_name][month_name]
            
            # Vectorized SPI calculation: Apply function to all 51 members at once
            spi_members = f_interp(precip_in_members.values)
            
            # Store results
            for member_num, spi_val in enumerate(spi_members):
                all_spi_forecasts.append({
                    'Station Name': station_name,
                    'Latitude': lat,
                    'Longitude': lon,
                    'Lead_Month': lead_month,
                    'Forecast_Month': month_name,
                    'Ensemble_Member': member_num,
                    'Forecast_SPI': spi_val
                })
                
    ds.close()
    print("SPI forecast calculation complete.")
    return pd.DataFrame(all_spi_forecasts)

# --- 4. Plotting Function (Maps) ---
def plot_forecast_map(gdf, plot_date, lead_month, timescale, output_path):
    """
    Plots a single forecast map for a given lead month.
    (Adapted from your Refined_SPI_Map_Generator.py)
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    try:
        counties = gpd.read_file(COUNTY_SHAPEFILE_PATH)
        counties = counties.to_crs(epsg=4326)
        counties.plot(ax=ax, facecolor='#F0F0F0', edgecolor='gray', linewidth=0.5, zorder=1)
    except Exception as e:
        print(f"Warning: Could not load county shapefile: {e}")
        ax.add_feature(cfeature.STATES, linewidth=1.5, edgecolor='black')

    spi_bins = [-np.inf, -2.0, -1.6, -1.3, -0.8, -0.5, 0.5, 0.8, 1.3, 1.6, 2.0, np.inf]
    spi_colors = ['#730000', '#E60000', '#FFA700', '#FCD37F', '#FFFF00', 
                  '#FFFFFF', '#ADFF2F', '#32CD32', '#009900', '#006400', '#0000FF']
    cmap = ListedColormap(spi_colors)
    norm = BoundaryNorm(spi_bins, cmap.N)

    ax.scatter(gdf['Longitude'], gdf['Latitude'], c=gdf['Mean_SPI'], 
               cmap=cmap, norm=norm, s=150, edgecolors='black', zorder=3, transform=ccrs.PlateCarree())

    legend_elements = [Patch(facecolor=spi_colors[i], edgecolor='k', label=label) for i, label in enumerate([
        '<= -2.0 (D4)', '-2.0 to -1.6 (D3)', '-1.6 to -1.3 (D2)',
        '-1.3 to -0.8 (D1)', '-0.8 to -0.5 (D0)', '-0.5 to 0.5 (Normal)',
        '0.5 to 0.8 (W0)', '0.8 to 1.3 (W1)', '1.3 to 1.6 (W2)',
        '1.6 to 2.0 (W3)', '>= 2.0 (W4)'
    ])]
    ax.legend(handles=legend_elements, loc='lower left', title="SPI Categories", fontsize=9, ncol=2)
    ax.set_title(f"Ensemble Mean {timescale}-Month SPI Forecast - Lead {lead_month} ({plot_date})", fontsize=16, fontweight='bold')
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Map saved: {output_path}")

# --- 5. Plotting Function (Meteograms) ---
def plot_station_meteogram(station_name, station_data, output_path):
    """
    Creates a box-and-whisker plot for a single station, showing SPI
    uncertainty across all 6 lead months.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Prepare data for boxplot: a list of arrays, one for each lead month
    data_to_plot = []
    month_labels = []
    for lead_month in sorted(station_data['Lead_Month'].unique()):
        spi_members = station_data[station_data['Lead_Month'] == lead_month]['Forecast_SPI']
        data_to_plot.append(spi_members.dropna())
        month_labels.append(f"Lead {lead_month}\n({station_data[station_data['Lead_Month'] == lead_month]['Forecast_Month'].iloc[0]})")
        
    ax.boxplot(data_to_plot, labels=month_labels, patch_artist=True,
               boxprops=dict(facecolor='lightblue', color='black'),
               medianprops=dict(color='red', linewidth=2),
               whiskerprops=dict(color='black', linestyle='--'),
               capprops=dict(color='black'))

    ax.axhline(0, color='gray', linestyle='--', linewidth=1, zorder=0) # Zero line
    ax.set_title(f"6-Month SPI Forecast Ensemble\n{station_name}", fontsize=16, fontweight='bold')
    ax.set_ylabel("Forecast SPI Value")
    ax.set_xlabel("Forecast Lead Time")
    ax.set_ylim(-4, 4) # Standard SPI range
    ax.grid(axis='y', linestyle=':', color='gray', alpha=0.7)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Meteogram saved: {output_path}")

# --- Main Execution ---
def main():
    # Create output directories
    MAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METEOGRAM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download data (or confirm it exists)
    download_seas_data()
    
    # 2. Load supporting data
    try:
        spi_df = pd.read_csv(SPI_THRESHOLDS_PATH)
        station_df = pd.read_csv(STATION_LOCATIONS_PATH)
        # Since output.csv has no station names, create them based on row index.
        # This assumes the order in output.csv matches the station order in the SPI conversion file.
        station_df['Station Name'] = [f"Station_{i}" for i in station_df.index]
        spi_df['Location'] = spi_df['Location'].astype('category').cat.codes.apply(lambda x: f"Station_{x}")
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: Missing input file: {e.filename}")
        print("Please ensure 'spi_to_rainfall_conversion.csv' and 'output.csv' are present.")
        exit()

    # 3. Create interpolators
    interpolators = create_spi_interpolators(spi_df)
    
    # 4. Process NetCDF and calculate all SPI forecasts
    spi_forecasts_df = generate_spi_forecasts(station_df, interpolators)
    
    if spi_forecasts_df.empty:
        print("No SPI forecasts were generated. Exiting.")
        return

    # 5. Generate Products
    print("\n--- Generating All Forecast Products ---")
    
    # Generate Maps (one for each lead month)
    for lead_month in sorted(spi_forecasts_df['Lead_Month'].unique()):
        # Get data for this lead month
        lm_data = spi_forecasts_df[spi_forecasts_df['Lead_Month'] == lead_month]
        
        # Calculate the ensemble mean SPI for each station
        mean_spi_by_station = lm_data.groupby('Station Name')['Forecast_SPI'].mean().reset_index()
        mean_spi_by_station = mean_spi_by_station.rename(columns={'Forecast_SPI': 'Mean_SPI'})
        
        # Merge with station locations
        gdf = pd.merge(station_df, mean_spi_by_station, on="Station Name")
        gdf = gpd.GeoDataFrame(gdf, geometry=gpd.points_from_xy(gdf.Longitude, gdf.Latitude), crs="EPSG:4326")
        
        plot_date = lm_data['Forecast_Month'].iloc[0]
        output_path = MAP_OUTPUT_DIR / f"spi_map_lead_{lead_month:02d}_{plot_date}.png"
        plot_forecast_map(gdf, plot_date, lead_month, 1, output_path)

    # Generate Meteograms (one for each station)
    for station_name in station_df['Station Name']:
        station_data = spi_forecasts_df[spi_forecasts_df['Station Name'] == station_name]
        if station_data.empty:
            continue
            
        # Clean station name for filename
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', station_name) + ".png"
        output_path = METEOGRAM_OUTPUT_DIR / safe_filename
        plot_station_meteogram(station_name, station_data, output_path)

    print("\n--- All Forecast Products Generated Successfully! ---")

if __name__ == "__main__":
    main()