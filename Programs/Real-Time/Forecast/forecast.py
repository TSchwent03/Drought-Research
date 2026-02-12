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
FORECAST_YEAR = '2026'
FORECAST_MONTH = '01' # Use '11' for November
FORECAST_AREA = [41, -96, 35, -88] # North, West, South, East (Missouri Box)
NETCDF_FILENAME = f"seas5_fc_{FORECAST_YEAR}_{FORECAST_MONTH}.nc"
NETCDF_FULL_PATH = OUTPUT_DIR / NETCDF_FILENAME

# --- 1. CDS API Data Download ---
def download_seas_data():
    """
    Downloads ECMWF SEAS5 ensemble forecast data using cdsapi.
    """
    if NETCDF_FULL_PATH.exists():
        # Check if the existing file contains ensemble members
        try:
            with xr.open_dataset(NETCDF_FULL_PATH) as ds:
                if 'number' in ds.dims:
                    print(f"Forecast file already exists and is valid: {NETCDF_FULL_PATH}")
                    return
                else:
                    print("Existing file is missing ensemble members. Deleting and re-downloading.")
        except Exception:
            print("Existing file is corrupt. Deleting and re-downloading.")
        
        os.remove(NETCDF_FULL_PATH)

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
                "product_type": "monthly_mean",
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
    Now supports 1, 3, and 6 month timescales.
    """
    print("Creating SPI interpolation functions...")
    interpolators = {}
    timescales = [1, 3, 6]
    
    for ts in timescales:
        interpolators[ts] = {}
        spi_subset = spi_df[spi_df['Timescale_Months'] == ts]
        
        for location in spi_subset['Location'].unique():
            interpolators[ts][location] = {}
            for month in spi_subset['Month'].unique():
                loc_month_data = spi_subset[(spi_subset['Location'] == location) & (spi_subset['Month'] == month)].sort_values('SPI_Value')
                if not loc_month_data.empty:
                    # Create the function: x=Rainfall, y=SPI
                    interpolators[ts][location][month] = interp1d(
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
        print(ds)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not open {NETCDF_FULL_PATH}. Was download successful?")
        print(f"Error: {e}")
        exit()

    start_month_idx = int(FORECAST_MONTH)
    start_year = int(FORECAST_YEAR)

    all_spi_forecasts = []

    print("Processing forecasts for all stations...")
    for _, station in station_df.iterrows():
        station_name = station['Station Name']
        lat = station['Latitude']
        lon = station['Longitude']
        
        # Extract the time series for this station from the xarray dataset
        station_ds = ds.sel(latitude=lat, longitude=lon, method='nearest')
        
        # Pre-calculate monthly precipitation (in inches) for all leads
        # Shape: (n_leads, n_members)
        monthly_precip_in = []
        valid_month_names = []

        for i, lead_month in enumerate(ds.forecastMonth.values):
            # Calculate correct month and year for this lead
            # lead_month is 1-based index from start
            # i is 0-based index
            
            # Calculate absolute month index (0-11) and year offset
            curr_month_abs = (start_month_idx + lead_month - 2) 
            curr_year = start_year + (curr_month_abs // 12)
            curr_month = (curr_month_abs % 12) + 2
            month_name = calendar.month_name[curr_month]
            valid_month_names.append(month_name)
            
            # Get rainfall rate (m/s) for all ensemble members
            precip_rate_members = station_ds['tprate'].sel(forecastMonth=lead_month)
            
            # Convert m/s to total inches for the month
            days_in_month = calendar.monthrange(curr_year, curr_month)[1]
            seconds_in_month = days_in_month * 24 * 60 * 60
            
            # Convert from rate (m/s) to total accumulation (m)
            precip_m_members = precip_rate_members * seconds_in_month
            # Convert meters to inches (1 meter = 39.3701 inches)
            precip_in_members = precip_m_members * 39.3701
            monthly_precip_in.append(precip_in_members.values)

        monthly_precip_in = np.array(monthly_precip_in) # Shape: (6, 51)

        # Calculate SPI for each timescale (1, 3, 6)
        for ts in [1, 3, 6]:
            if ts not in interpolators or station_name not in interpolators[ts]:
                continue
            
            for i, lead_month in enumerate(ds.forecastMonth.values):
                # Check if we have enough forecast history for this timescale
                # We need 'ts' months of data ending at index 'i'
                start_idx = i - ts + 1
                if start_idx < 0:
                    continue # Cannot calculate e.g. 3-month SPI at Lead 1 without antecedent data
                
                # Sum precipitation over the window [start_idx, i]
                window_precip = np.sum(monthly_precip_in[start_idx : i+1, :], axis=0)
                
                month_name = valid_month_names[i]
                
                if month_name not in interpolators[ts][station_name]:
                    continue

                f_interp = interpolators[ts][station_name][month_name]
                spi_members = f_interp(window_precip)
                
                for member_num, spi_val in enumerate(spi_members):
                    all_spi_forecasts.append({
                        'Station Name': station_name,
                        'Latitude': lat,
                        'Longitude': lon,
                        'Lead_Month': lead_month,
                        'Forecast_Month': month_name,
                        'Timescale': ts,
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
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    try:
        counties = gpd.read_file(COUNTY_SHAPEFILE_PATH)
        counties = counties.to_crs(epsg=4326)
        counties.plot(ax=ax, facecolor='white', edgecolor='black', linewidth=1.2, zorder=1)
    except Exception as e:
        print(f"Warning: Could not load county shapefile: {e}")
        ax.add_feature(cfeature.STATES, linewidth=1.5, edgecolor='black')

    spi_bins = [-np.inf, -2.0, -1.6, -1.3, -0.8, -0.5, 0.5, 0.8, 1.3, 1.6, 2.0, np.inf]
    spi_colors = [
        '#730000', '#E60000', '#E69800', '#FED37F', '#FEFE00', 
        '#FFFFFF', '#AAF596', '#4CE600', '#38A800', '#145A00', '#002673'
    ]
    cmap = ListedColormap(spi_colors)
    norm = BoundaryNorm(spi_bins, cmap.N)

    ax.scatter(gdf['Longitude'], gdf['Latitude'], c=gdf['Mean_SPI'], 
               cmap=cmap, norm=norm, s=150, edgecolors='black', zorder=3, transform=ccrs.PlateCarree())

    legend_elements = [
        Patch(facecolor=spi_colors[i], edgecolor='k', label=label) for i, label in enumerate([
            '<= D4 Exceptional Drought)', 'D3 Extreme Drought', 'D2 Severe Drought',
            'D1 Moderate Drought', 'D0 Abnormally Dry', 'Near Normal',
            'W0 Abnormally Wet', 'W1 Moderately Wet', 'W2 Severely Wet',
            'W3 Extremely Wet', 'W4 Exceptionally Wet'
        ])
    ]
    ax.legend(handles=legend_elements, title="SPI Categories", fontsize=10, title_fontsize=11, loc='upper left', bbox_to_anchor=(1, 1))
    ax.set_title(f"Ensemble Mean {timescale}-Month SPI Forecast - Lead {lead_month} ({plot_date})", fontsize=16)
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Map saved: {output_path}")

# --- 5. Plotting Function (Meteograms) ---
def plot_station_meteogram(station_name, station_data, timescale, output_path):
    """
    Creates a box-and-whisker plot for a single station, showing SPI
    uncertainty across all 6 lead months.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Prepare data for boxplot: a list of arrays, one for each lead month
    data_to_plot = []
    month_labels = []
    for lead_month in sorted(station_data['Lead_Month'].unique()):
        spi_members = station_data[station_data['Lead_Month'] == lead_month]['Forecast_SPI']
        data_to_plot.append(spi_members.dropna())
        month_labels.append(f"Lead {lead_month}\n({station_data[station_data['Lead_Month'] == lead_month]['Forecast_Month'].iloc[0]})")

    # Define SPI Categories and Colors (Same as Map)
    spi_bins = [-np.inf, -2.0, -1.6, -1.3, -0.8, -0.5, 0.5, 0.8, 1.3, 1.6, 2.0, np.inf]
    spi_colors = [
        '#730000', '#E60000', '#E69800', '#FED37F', '#FEFE00', 
        '#FFFFFF', '#AAF596', '#4CE600', '#38A800', '#145A00', '#002673'
    ]
    spi_labels = [
        'D4 Exceptional Drought', 'D3 Extreme Drought', 'D2 Severe Drought',
        'D1 Moderate Drought', 'D0 Abnormally Dry', 'Near Normal',
        'W0 Abnormally Wet', 'W1 Moderately Wet', 'W2 Severely Wet',
        'W3 Extremely Wet', 'W4 Exceptionally Wet'
    ]

    legend_elements = []
    for i in range(len(spi_colors)):
        low = spi_bins[i]
        high = spi_bins[i+1]
        color = spi_colors[i]
        
        # Handle infinity for plotting bounds
        plot_low = -10 if low == -np.inf else low
        plot_high = 10 if high == np.inf else high
        
        ax.axhspan(plot_low, plot_high, facecolor=color, alpha=0.3, zorder=0)
        legend_elements.append(Patch(facecolor=color, edgecolor='black', label=spi_labels[i], alpha=0.3))

    ax.boxplot(data_to_plot, labels=month_labels, patch_artist=True,
               boxprops=dict(facecolor='white', color='black'),
               medianprops=dict(color='black', linewidth=2),
               whiskerprops=dict(color='black', linestyle='--'),
               capprops=dict(color='black'), zorder=3)

    ax.axhline(0, color='black', linestyle='--', linewidth=1, zorder=2) # Zero line
    ax.set_title(f"{timescale}-Month SPI Forecast Ensemble\n{station_name}", fontsize=16, fontweight='bold')
    ax.set_ylabel("Forecast SPI Value")
    ax.set_xlabel("Forecast Lead Time")
    ax.set_ylim(-2.5, 2.5)
    ax.grid(axis='y', linestyle=':', color='black', alpha=0.3, zorder=1)
    
    # Add Legend
    ax.legend(handles=legend_elements, title="SPI Categories", fontsize=10, title_fontsize=11, loc='upper left', bbox_to_anchor=(1, 1))
    
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
        
        # Assign real station names
        # We assume the rows in output.csv correspond to the alphabetically sorted locations in the SPI file.
        unique_stations = sorted(spi_df['Location'].unique())
        if len(station_df) == len(unique_stations):
            station_df['Station Name'] = unique_stations
        else:
            print("Warning: Station count mismatch. Using generic station names.")
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
    
    # Loop through timescales to generate products for each
    for timescale in [1, 3, 6]:
        print(f"\nGenerating products for {timescale}-Month SPI...")
        ts_data = spi_forecasts_df[spi_forecasts_df['Timescale'] == timescale]
        
        if ts_data.empty:
            print(f"No data for {timescale}-Month SPI (likely due to lead time constraints).")
            continue

        # Generate Maps (one for each valid lead month)
        for lead_month in sorted(ts_data['Lead_Month'].unique()):
            lm_data = ts_data[ts_data['Lead_Month'] == lead_month]
            
            # Calculate the ensemble mean SPI for each station
            mean_spi_by_station = lm_data.groupby('Station Name')['Forecast_SPI'].mean().reset_index()
            mean_spi_by_station = mean_spi_by_station.rename(columns={'Forecast_SPI': 'Mean_SPI'})
            
            # Merge with station locations
            gdf = pd.merge(station_df, mean_spi_by_station, on="Station Name")
            gdf = gpd.GeoDataFrame(gdf, geometry=gpd.points_from_xy(gdf.Longitude, gdf.Latitude), crs="EPSG:4326")
            
            plot_date = lm_data['Forecast_Month'].iloc[0]
            output_path = MAP_OUTPUT_DIR / f"spi_{timescale}mo_map_lead_{lead_month:02d}_{plot_date}.png"
            plot_forecast_map(gdf, plot_date, lead_month, timescale, output_path)

        # Generate Meteograms (one for each station)
        for station_name in station_df['Station Name']:
            station_data = ts_data[ts_data['Station Name'] == station_name]
            if station_data.empty:
                continue
                
            # Clean station name for filename
            safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', station_name) + f"_spi_{timescale}mo.png"
            output_path = METEOGRAM_OUTPUT_DIR / safe_filename
            plot_station_meteogram(station_name, station_data, timescale, output_path)

    print("\n--- All Forecast Products Generated Successfully! ---")

if __name__ == "__main__":
    main()