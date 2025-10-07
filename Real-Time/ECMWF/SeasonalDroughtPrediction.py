import cdsapi
import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import numpy as np
import pandas as pd

# --- Define the download directory and filename ---
download_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Real-Time\ECMWF\SEAS"
filename = "seas5_total_precipitation_2025_10.grib"
full_path = os.path.join(download_dir, filename)

def SEASdata():
    # --- Create the directory if it does not exist ---
    os.makedirs(download_dir, exist_ok=True)

    dataset = "seasonal-monthly-single-levels"
    request = {
        "originating_centre": "ecmwf",
        "system": "51",
        "variable": ["total_precipitation"],
        "year": ["2025"],
        "month": ["10"],
        "leadtime_month": [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6"
        ],
        "data_format": "grib",
        "product_type": [
            "ensemble_mean",
            "monthly_mean",
            "monthly_maximum",
            "monthly_standard_deviation"
        ],
        "area": [41, -96, 35, -88]
    }

    client = cdsapi.Client()
    client.retrieve(dataset, request, full_path)

def SEASmap():
    # --- Step 1: Open the GRIB file using xarray ---
    try:
        # Use backend_kwargs to specify which data field to open (monthly_mean = fcmean)
        ds = xr.open_dataset(
            full_path, 
            engine='cfgrib',
            backend_kwargs={'filter_by_keys': {'dataType': 'fcmean'}}
        )
    except Exception as e:
        print(f"Error opening GRIB file: {e}")
        exit()

    # --- Step 2: Sum the monthly precipitation over 6 months ---
    # The variable is 'tprate', representing a rate in m/s.
    tprate_data = ds['tprate']

    # The `step` coordinate corresponds to the lead month.
    # The forecast is for Oct 2025 (leadtime 1) to Mar 2026 (leadtime 6).
    # For simplicity, we use a static list for the number of seconds in each month.
    # (days * 24 hours/day * 60 min/hour * 60 sec/min)
    monthly_seconds = [
        31 * 24 * 60 * 60,  # October
        30 * 24 * 60 * 60,  # November
        31 * 24 * 60 * 60,  # December
        31 * 24 * 60 * 60,  # January
        28 * 24 * 60 * 60,  # February (non-leap year)
        31 * 24 * 60 * 60   # March
    ]

    # Calculate the total precipitation for each month
    # `isel` is used here to select each step (0 to 5) corresponding to the 6 lead months.
    # We also use `number=0` to select the ensemble mean, since your request included it.
    monthly_totals = [
        tprate_data.isel(number=0, step=i) * monthly_seconds[i]
        for i in range(len(monthly_seconds))
    ]

    # Sum the monthly totals to get the 6-month total
    total_6_month_precip = sum(monthly_totals)

    # Convert meters to inches for easier interpretation (1 inch = 25.4 mm)
    total_6_month_precip_in = total_6_month_precip * 1000 / 25.4

    # --- Step 3: Create the map and plot the data ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Plot the data using pcolormesh
    total_6_month_precip_in.plot.pcolormesh(
        ax=ax,
        cmap='Greens',
        transform=ccrs.PlateCarree(),
        x='longitude',
        y='latitude',
        cbar_kwargs={'label': 'Total 6-Month Precipitation (in)'}
    )

    # Add map features
    ax.coastlines('10m')
    ax.add_feature(cartopy.feature.BORDERS)
    ax.add_feature(cartopy.feature.STATES, linestyle='-')
    ax.set_title('6-Month Total Precipitation Forecast (Oct 2025 - Mar 2026)')

    # Set the extent to match your request area
    ax.set_extent([-96, -88, 35, 41], crs=ccrs.PlateCarree())

    plt.show()

try:
    # Open the GRIB file, filtering for ensemble members ('em')
    ds = xr.open_dataset(
        full_path, 
        engine='cfgrib',
        backend_kwargs={'filter_by_keys': {'dataType': 'em'}}
    )
except Exception as e:
    print(f"Error opening GRIB file: {e}")
    exit()

# --- Step 2: Define station location and extract data ---
station_name = 'Columbia'
lat, lon = 38.9517, -92.3341 # Coordinates for Columbia, MO

# Extract the precipitation rate data ('tprate') for the nearest grid point
tprate_station = ds['tprate'].sel(latitude=lat, longitude=lon, method='nearest')

# --- Step 3: Accumulate precipitation for lead times ---
# The forecast starts in Oct 2025 (leadtime 1), so leadtimes 1-6 cover Oct-Mar.
monthly_seconds = np.array([
    31, 30, 31, 31, 28, 31 # Number of days for Oct 2025 - Mar 2026
]) * 24 * 60 * 60

# Monthly totals (m) for each ensemble member
monthly_totals_m = tprate_station * monthly_seconds

# 1-month total: First month
precip_1m = monthly_totals_m.isel(step=0)

# 3-month total: Sum of first 3 months
precip_3m = monthly_totals_m.isel(step=slice(0, 3)).sum(dim='step')

# 6-month total: Sum of all 6 months
precip_6m = monthly_totals_m.sum(dim='step')

# Convert to millimeters for readability
precip_1m_mm = precip_1m * 1000
precip_3m_mm = precip_3m * 1000
precip_6m_mm = precip_6m * 1000

# --- Step 4: Prepare data for plotting and create the plot ---
data_to_plot = [
    precip_1m_mm.values,
    precip_3m_mm.values,
    precip_6m_mm.values
]

labels = ['1-Month Total', '3-Month Total', '6-Month Total']
positions = [1, 3, 6] # Corrected: positions must match the number of datasets

fig, ax = plt.subplots(figsize=(10, 8))

# The data list and positions list now have the same length (3)
ax.boxplot(data_to_plot, positions=positions, widths=0.6, patch_artist=True)

ax.set_title(f'Ensemble Precipitation Meteogram for {station_name} (Oct 2025 Start)', fontsize=16)
ax.set_xlabel('Lead Time (Months)', fontsize=12)
ax.set_ylabel('Total Precipitation (mm)', fontsize=12)
ax.set_xticks(positions)
ax.set_xticklabels(labels)
ax.set_xlim(0, 7)
ax.grid(True, linestyle=':', alpha=0.6)

plt.show()