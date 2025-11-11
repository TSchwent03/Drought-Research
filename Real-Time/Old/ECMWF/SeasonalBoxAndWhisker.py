import os
import cdsapi
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import numpy as np
import pandas as pd
from scipy import stats

download_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Real-Time\ECMWF\SEAS"

def SEASdata_ensemble_members():
    filename = "seas5_total_precipitation_2023_10_ensemble_members.nc" # Use .nc for NetCDF
    full_path = os.path.join(download_dir, filename)

    os.makedirs(download_dir, exist_ok=True)

    dataset = "seasonal-monthly-single-levels" # Corrected dataset name for re-forecasts
    request = {
        "originating_centre": "ecmwf",
        "system": "51",
        "variable": ["total_precipitation"],
        "year": ["2025"], # Use a past year for hindcast data
        "month": ["10"],
        "leadtime_month": [
            "1", "2", "3", "4", "5", "6"
        ],
        "data_format": "netcdf", # Request NetCDF format
        "product_type": ["ensemble_members"], # Request individual members
        "area": [41, -96, 35, -88]
    }

    client = cdsapi.Client()
    client.retrieve(dataset, request, full_path)
    return full_path

def PlotBoxAndWhisker_from_members():
    # --- Define the new filename and path ---
    filename = "seas5_total_precipitation_2023_10_ensemble_members.nc"
    full_path = os.path.join(download_dir, filename)

    # --- Step 1: Open the NetCDF file containing all ensemble members ---
    try:
        print(f"Reading ensemble members from {filename}...")
        ds = xr.open_dataset(full_path)
        print(f"Dataset dimensions: {ds.dims}")
    except Exception as e:
        print(f"Error opening NetCDF file: {e}")
        return
    # --- Step 2: Sum the monthly precipitation over 6 months ---
    monthly_seconds = [
        31 * 24 * 60 * 60,  # October 2025
        30 * 24 * 60 * 60,  # November 2025
        31 * 24 * 60 * 60,  # December 2025
        31 * 24 * 60 * 60,  # January 2026
        28 * 24 * 60 * 60,  # February 2026
        31 * 24 * 60 * 60   # March 2026
    ]

    tprate_data = ds['tprate']
    
    # Explicitly calculate the total for each month before summing
    total_precip_monthly = tprate_data * xr.DataArray(monthly_seconds, dims=['forecastMonth'], coords={'forecastMonth': tprate_data['forecastMonth']})
    
    # Now sum the monthly totals across the forecastMonth dimension for each member
    # The result will still have the 'number' dimension.
    total_6_month_precip = total_precip_monthly.sum(dim='forecastMonth')

    # Convert meters to inches
    total_6_month_precip_in = total_6_month_precip * 1000 / 25.4
    
    # --- Step 3: Define a point of interest and get all ensemble member values ---
    lat, lon = 38.95, -92.33 # Columbia, MO
    
    # Select the data for each ensemble member at the specified location
    ensemble_data = total_6_month_precip_in.sel(latitude=lat, longitude=lon, method='nearest')
    
    # --- Step 4: Create the box plot using the raw ensemble data ---
    fig, ax = plt.subplots(figsize=(6, 8))
    
    # The .values attribute gets the NumPy array of all members for the box plot
    ax.boxplot(ensemble_data.values, showfliers=True)
    
    ax.set_title(f'6-Month Total Precipitation Hindcast (Oct 2025 - Mar 2026)\nfor Location: ({lat}, {lon})')
    ax.set_ylabel('Total Precipitation (inches)')
    ax.set_xticks([1])
    ax.set_xticklabels(['Forecast'])
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

#SEASdata_ensemble_members()
PlotBoxAndWhisker_from_members()