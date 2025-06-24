import cdsapi
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import calendar
import numpy as np

# --- Configuration ---
# Bounding box for Missouri
AREA_BOUNDS = [40.6, -95.8, 36.5, -89.1] # [North, West, South, East]

# Forecast settings
FORECAST_YEAR = '2024' # Use a year for which data exists
FORECAST_MONTH = '09' # A September forecast...
TARGET_MONTHS = ['10', '11', '12'] # ...for the Oct-Nov-Dec season
OUTPUT_FILE = f'missouri_precip_OND_{FORECAST_YEAR}_from_{FORECAST_MONTH}.nc' # More descriptive filename

# --- Helper Functions ---
def calculate_lead_times(forecast_month_str, target_months_str):
    """Calculates lead times, handling year boundaries."""
    forecast_month = int(forecast_month_str)
    # A more robust formula that correctly handles all month combinations
    # and always produces a lead time between 1 and 12.
    return [str(((int(m) - forecast_month - 1 + 12) % 12) + 1) for m in target_months_str]

LEAD_TIMES = calculate_lead_times(FORECAST_MONTH, TARGET_MONTHS)

# --- Step 1: Request a Geographic Subset from the CDS API ---
if not os.path.exists(OUTPUT_FILE):
    print("Requesting regional subset from Copernicus CDS...")
    c = cdsapi.Client()
    c.retrieve(
        # For forecast anomalies, we use a different dataset
        'seasonal-monthly-single-levels',
        {
            'originating_centre': 'ecmwf',
            'system': '5',
            # The long name can fail. The short name 'tpara' is more reliable
            # and matches the variable name inside the resulting NetCDF file.
            'variable': 'tpara',
            'product_type': 'monthly_mean_anomalies',
            'year': FORECAST_YEAR,
            'month': FORECAST_MONTH,
            'leadtime_month': LEAD_TIMES,
            'area': AREA_BOUNDS, # <-- This is the key change!
            'format': 'netcdf',
        },
        OUTPUT_FILE)
    print(f"Download of small regional file is complete.")
else:
    print(f"Using existing file: {OUTPUT_FILE}")

# --- Step 2: Open the Subset and Process for Plotting ---
print("Processing data...")
with xr.open_dataset(OUTPUT_FILE) as ds:
    # Average the anomaly across the three lead months to get a seasonal value
    seasonal_anomaly = ds['tpara'].mean(dim='leadtime_month')
    
    # Average across all the ensemble members to get the mean forecast anomaly
    mean_seasonal_anomaly = seasonal_anomaly.mean(dim='number')
    
    # Calculate a more accurate days/month average for the target season
    days_in_months = [calendar.monthrange(int(FORECAST_YEAR), int(m))[1] for m in TARGET_MONTHS]
    avg_days_in_month = np.mean(days_in_months)

    # Convert from meters/day to inches/month for a more intuitive map label
    mean_seasonal_anomaly_in_per_month = mean_seasonal_anomaly * avg_days_in_month * 39.3701

# --- Step 3: Create the Map with Cartopy ---
print("Creating map...")
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mercator())

# Plot the data
# Use a divergent colormap (e.g., BrBG) for anomalies
plot = mean_seasonal_anomaly_in_per_month.plot(
    ax=ax,
    transform=ccrs.PlateCarree(), # Tell Cartopy the data is in lat/lon coordinates
    cmap='BrBG',
    add_colorbar=False # We'll add a custom one
)

# Add a proper colorbar
cbar = plt.colorbar(plot, ax=ax, orientation='vertical', shrink=0.7)
cbar.set_label('Precipitation Anomaly (inches/month)', fontsize=12)

# Add geographic features
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=1.5)

# Set map extent to our requested area with a little buffer
ax.set_extent([AREA_BOUNDS[1], AREA_BOUNDS[3], AREA_BOUNDS[2], AREA_BOUNDS[0]], crs=ccrs.PlateCarree())

ax.set_title(f'Mean Seasonal Precipitation Anomaly Forecast\n(Oct-Nov-Dec {FORECAST_YEAR}, Forecast from {calendar.month_name[int(FORECAST_MONTH)]})', fontsize=16)

plt.show()